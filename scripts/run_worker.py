import argparse
import asyncio
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "apps" / "api"))

from app.db import SessionFactory
from app.domain.models import OutboxEvent
from app.config import Settings, get_settings
from app.intake.service import anonymize_expired_submissions
from app.domain.models import InternshipUpload
from app.internships.storage import LocalInternshipStorage, SupabaseInternshipStorage
from app.internships.uploads.scanning import ClamAVScanner, scan_with_clamav
from app.notifications.service import process_pending_notifications
from app.outbox.service import process_one
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


async def process_retention_sweep(session: AsyncSession) -> tuple[int, int]:
    pending = await session.scalar(
        select(OutboxEvent)
        .where(
            OutboxEvent.event_type == "RetentionSweepRequested",
            OutboxEvent.status == "PENDING",
        )
        .order_by(OutboxEvent.created_at)
    )
    if pending is None:
        pending = OutboxEvent(
            event_type="RetentionSweepRequested",
            aggregate_type="public_intake",
            aggregate_id=uuid.uuid4(),
            payload={"requested_at": datetime.now(UTC).isoformat()},
        )
        session.add(pending)
        await session.commit()

    async def handler(_: dict[str, object]) -> None:
        await anonymize_expired_submissions(session, now=datetime.now(UTC))

    try:
        await process_one(
            session,
            handlers={"RetentionSweepRequested": handler},
            event_id=pending.id,
        )
        return 1, 0
    except Exception:
        return 0, 1


async def process_malware_scans(
    session: AsyncSession, *, limit: int, settings: Settings
) -> tuple[int, int]:
    events = list(
        (
            await session.scalars(
                select(OutboxEvent)
                .where(
                    OutboxEvent.event_type == "MalwareScanRequested",
                    OutboxEvent.status == "PENDING",
                )
                .order_by(OutboxEvent.created_at)
                .limit(limit)
            )
        ).all()
    )
    succeeded = 0
    failed = 0
    for event in events:

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
                content = await SupabaseInternshipStorage(settings).read(
                    upload.storage_key
                )
            else:
                content = LocalInternshipStorage(
                    settings.internship_local_storage_path
                ).read(upload.storage_key)
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
                event_id=event.id,
            )
            succeeded += 1
        except Exception:
            failed += 1
            await session.refresh(event)
            if event.attempts >= 5:
                upload = await session.scalar(
                    select(InternshipUpload).where(
                        InternshipUpload.upload_id == event.payload.get("upload_id")
                    )
                )
                if upload is not None:
                    upload.state = "SCAN_FAILED"
                    upload.scan_message = "Malware scan failed after bounded retries"
                    await session.commit()
    return succeeded, failed


async def run(*, limit: int) -> int:
    settings = get_settings()
    async with SessionFactory() as session:
        succeeded, failed = await process_pending_notifications(session, limit=limit)
        scan_succeeded, scan_failed = await process_malware_scans(
            session, limit=limit, settings=settings
        )
        retention_succeeded, retention_failed = await process_retention_sweep(session)
    print(
        f"Notification jobs: {succeeded} succeeded, {failed} failed; "
        f"malware scans: {scan_succeeded} succeeded, {scan_failed} failed; "
        f"retention jobs: {retention_succeeded} succeeded, {retention_failed} failed"
    )
    return 1 if failed or retention_failed else 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Process pending PraxisAI outbox jobs once."
    )
    parser.add_argument("--limit", type=int, default=100)
    args = parser.parse_args()
    if not 1 <= args.limit <= 1_000:
        parser.error("--limit must be between 1 and 1000")
    return asyncio.run(run(limit=args.limit))


if __name__ == "__main__":
    raise SystemExit(main())
