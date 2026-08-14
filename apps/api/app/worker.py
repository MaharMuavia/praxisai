import argparse
import asyncio
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import and_, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.db import SessionFactory
from app.domain.models import InternshipUpload, JobAttempt, OutboxEvent
from app.intake.service import anonymize_expired_submissions
from app.internships.storage import (
    LocalInternshipStorage,
    SupabaseInternshipStorage,
    SupabaseStorageError,
)
from app.internships.uploads.scanning import ClamAVScanner, scan_with_clamav
from app.notifications.service import process_pending_notifications
from app.outbox.service import OutboxEventAlreadyRunning, process_one

RETENTION_EVENT_NAMESPACE = uuid.UUID("c2c058a4-9e8f-483b-ac82-9913d6f18177")


@dataclass(frozen=True)
class WorkerOutcome:
    notifications_succeeded: int
    notifications_failed: int
    malware_scans_succeeded: int
    malware_scans_failed: int
    retention_sweeps_succeeded: int
    retention_sweeps_failed: int

    @property
    def exit_code(self) -> int:
        return int(
            any(
                (
                    self.notifications_failed,
                    self.malware_scans_failed,
                    self.retention_sweeps_failed,
                )
            )
        )

    def summary(self) -> str:
        return (
            f"Notification jobs: {self.notifications_succeeded} succeeded, "
            f"{self.notifications_failed} failed; "
            f"malware scans: {self.malware_scans_succeeded} succeeded, "
            f"{self.malware_scans_failed} failed; "
            f"retention jobs: {self.retention_sweeps_succeeded} succeeded, "
            f"{self.retention_sweeps_failed} failed"
        )


async def _delete_quarantined_object(settings: Settings, storage_key: str) -> bool:
    try:
        if settings.storage_provider == "supabase":
            await SupabaseInternshipStorage(settings).delete(storage_key)
        else:
            LocalInternshipStorage(settings.internship_local_storage_path).delete(storage_key)
    except (OSError, ValueError, SupabaseStorageError):
        return False
    return True


async def _expire_abandoned_uploads(
    session: AsyncSession,
    *,
    settings: Settings,
    now: datetime,
    limit: int,
) -> int:
    uploads = list(
        (
            await session.scalars(
                select(InternshipUpload)
                .where(
                    or_(
                        and_(
                            InternshipUpload.expires_at <= now - timedelta(hours=24),
                            InternshipUpload.state.notin_(
                                ["ATTACHED", "EXPIRED", "EXPIRED_CLEANUP_PENDING"]
                            ),
                        ),
                        and_(
                            InternshipUpload.expires_at <= now,
                            InternshipUpload.state.in_(
                                ["EXPIRED_CLEANUP_PENDING", "REJECTED_CLEANUP_PENDING"]
                            ),
                        ),
                    )
                )
                .order_by(InternshipUpload.expires_at)
                .limit(limit)
                .with_for_update(skip_locked=True)
            )
        ).all()
    )
    for upload in uploads:
        terminal_state = "REJECTED" if upload.state == "REJECTED_CLEANUP_PENDING" else "EXPIRED"
        if not await _delete_quarantined_object(settings, upload.storage_key):
            raise RuntimeError("Upload object cleanup failed")
        upload.state = terminal_state
        upload.scan_message = (
            "Rejected upload object cleanup completed"
            if terminal_state == "REJECTED"
            else "Expired by the abandoned-upload retention policy"
        )
    return len(uploads)


async def process_retention_sweep(
    session: AsyncSession, *, limit: int, settings: Settings
) -> tuple[int, int]:
    pending_id = await session.scalar(
        select(OutboxEvent.id)
        .where(
            OutboxEvent.event_type == "RetentionSweepRequested",
            OutboxEvent.status == "PENDING",
            OutboxEvent.available_at <= datetime.now(UTC),
        )
        .order_by(OutboxEvent.created_at)
    )
    if pending_id is None:
        now = datetime.now(UTC)
        bucket_start = now.replace(minute=0, second=0, microsecond=0)
        event_id = uuid.uuid5(RETENTION_EVENT_NAMESPACE, bucket_start.isoformat())
        existing = await session.get(OutboxEvent, event_id)
        if existing is not None:
            if existing.status in {"RUNNING", "SUCCEEDED"}:
                return 0, 0
            if existing.status != "PENDING":
                return 0, 1
            pending_id = existing.id
        else:
            pending = OutboxEvent(
                id=event_id,
                event_type="RetentionSweepRequested",
                aggregate_type="public_intake",
                aggregate_id=event_id,
                payload={"requested_at": datetime.now(UTC).isoformat()},
            )
            session.add(pending)
            try:
                await session.commit()
                pending_id = pending.id
            except IntegrityError:
                await session.rollback()
                existing = await session.get(OutboxEvent, event_id)
                if existing is None:
                    raise
                if existing.status in {"RUNNING", "SUCCEEDED"}:
                    return 0, 0
                if existing.status != "PENDING":
                    return 0, 1
                pending_id = existing.id

    async def handler(_: dict[str, object]) -> None:
        now = datetime.now(UTC)
        await anonymize_expired_submissions(session, now=now, limit=limit)
        await _expire_abandoned_uploads(session, settings=settings, now=now, limit=limit)

    try:
        await process_one(
            session,
            handlers={"RetentionSweepRequested": handler},
            event_id=pending_id,
        )
        return 1, 0
    except OutboxEventAlreadyRunning:
        return 0, 0
    except Exception:
        return 0, 1


async def process_malware_scans(
    session: AsyncSession, *, limit: int, settings: Settings
) -> tuple[int, int]:
    event_ids = list(
        (
            await session.scalars(
                select(OutboxEvent.id)
                .where(
                    OutboxEvent.event_type == "MalwareScanRequested",
                    OutboxEvent.status == "PENDING",
                    OutboxEvent.available_at <= datetime.now(UTC),
                )
                .order_by(OutboxEvent.created_at)
                .limit(limit)
            )
        ).all()
    )
    succeeded = 0
    failed = 0
    for event_id in event_ids:

        async def handler(payload: dict[str, object]) -> None:
            upload_id = payload.get("upload_id")
            if not isinstance(upload_id, str):
                raise ValueError("Malware scan event has no upload ID")
            upload = await session.scalar(
                select(InternshipUpload)
                .where(InternshipUpload.upload_id == upload_id)
                .with_for_update()
            )
            if upload is None:
                raise ValueError("Upload for malware scan was deleted")
            if upload.state in {"CLEAN", "REJECTED", "ATTACHED", "EXPIRED"}:
                return
            if settings.upload_scanner_provider != "clamav" or not settings.clamav_host:
                raise RuntimeError("ClamAV scanner is not configured")
            upload.state = "SCANNING"
            await session.flush()
            if settings.storage_provider == "supabase":
                content = await SupabaseInternshipStorage(settings).read(upload.storage_key)
            else:
                content = LocalInternshipStorage(settings.internship_local_storage_path).read(
                    upload.storage_key
                )
            scanner = ClamAVScanner(
                lambda value: scan_with_clamav(
                    value,
                    host=settings.clamav_host or "",
                    port=settings.clamav_port,
                    timeout_seconds=settings.scan_timeout_seconds,
                )
            )
            result = await asyncio.to_thread(
                scanner.scan,
                content,
                declared_content_type=upload.content_type,
                filename=upload.filename,
            )
            if result.state == "REJECTED" and not await _delete_quarantined_object(
                settings, upload.storage_key
            ):
                raise RuntimeError("Rejected upload object cleanup failed")
            upload.state = result.state
            upload.scan_provider = "clamav"
            upload.scanned_at = datetime.now(UTC)
            upload.scan_message = result.message
            upload.scan_evidence = {
                "provider": "clamav",
                "sha256": upload.sha256,
                "message": result.message,
            }

        try:
            await process_one(
                session,
                handlers={"MalwareScanRequested": handler},
                event_id=event_id,
            )
            succeeded += 1
        except OutboxEventAlreadyRunning:
            continue
        except Exception:
            failed += 1
            event = await session.get(OutboxEvent, event_id, populate_existing=True)
            if event is None:
                continue
            if event.attempts >= 5:
                upload = await session.scalar(
                    select(InternshipUpload).where(
                        InternshipUpload.upload_id == event.payload.get("upload_id")
                    )
                )
                if upload is not None:
                    upload.state = "SCAN_FAILED"
                    upload.scan_message = "Malware scan failed after bounded retries"
                    if not await _delete_quarantined_object(settings, upload.storage_key):
                        upload.scan_message = (
                            "Malware scan failed after bounded retries; quarantined object "
                            "cleanup also failed"
                        )
                    await session.commit()
    return succeeded, failed


async def requeue_stale_running_events(
    session: AsyncSession, *, stale_after: timedelta, now: datetime | None = None
) -> int:
    recovered_at = now or datetime.now(UTC)
    cutoff = recovered_at - stale_after
    events = list(
        (
            await session.scalars(
                select(OutboxEvent)
                .where(
                    OutboxEvent.status == "RUNNING",
                    OutboxEvent.updated_at <= cutoff,
                )
                .with_for_update()
            )
        ).all()
    )
    for event in events:
        event.status = "PENDING"
        event.available_at = recovered_at
        event.last_error = "Worker execution ended before the outbox event completed"
        attempts = list(
            (
                await session.scalars(
                    select(JobAttempt).where(
                        JobAttempt.outbox_event_id == event.id,
                        JobAttempt.status == "RUNNING",
                    )
                )
            ).all()
        )
        for attempt in attempts:
            attempt.status = "FAILED"
            attempt.finished_at = recovered_at
            attempt.error_category = "StaleWorkerClaim"
            attempt.error_message = event.last_error
    if events:
        await session.commit()
    return len(events)


async def process_worker_batch(
    session: AsyncSession, *, limit: int, settings: Settings
) -> WorkerOutcome:
    notifications_succeeded, notifications_failed = await process_pending_notifications(
        session, limit=limit
    )
    malware_scans_succeeded, malware_scans_failed = await process_malware_scans(
        session, limit=limit, settings=settings
    )
    retention_sweeps_succeeded, retention_sweeps_failed = await process_retention_sweep(
        session, limit=limit, settings=settings
    )
    return WorkerOutcome(
        notifications_succeeded=notifications_succeeded,
        notifications_failed=notifications_failed,
        malware_scans_succeeded=malware_scans_succeeded,
        malware_scans_failed=malware_scans_failed,
        retention_sweeps_succeeded=retention_sweeps_succeeded,
        retention_sweeps_failed=retention_sweeps_failed,
    )


async def run(*, limit: int) -> int:
    settings = get_settings()
    async with SessionFactory() as session:
        recovered = await requeue_stale_running_events(
            session,
            stale_after=timedelta(seconds=settings.outbox_stale_after_seconds),
        )
        outcome = await process_worker_batch(session, limit=limit, settings=settings)
    if recovered:
        print(f"Recovered {recovered} stale outbox claim(s)")
    print(outcome.summary())
    return outcome.exit_code


def main() -> int:
    parser = argparse.ArgumentParser(description="Process pending PraxisAI outbox jobs once.")
    parser.add_argument("--limit", type=int, default=100)
    args = parser.parse_args()
    if not 1 <= args.limit <= 1_000:
        parser.error("--limit must be between 1 and 1000")
    return asyncio.run(run(limit=args.limit))


if __name__ == "__main__":
    raise SystemExit(main())
