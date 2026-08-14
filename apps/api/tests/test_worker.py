import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app import worker
from app.config import Settings
from app.domain.models import Base, InternshipUpload, JobAttempt, OutboxEvent
from app.worker import WorkerOutcome


@pytest.mark.asyncio
async def test_worker_batch_orchestrates_every_processor(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = AsyncMock(spec=AsyncSession)
    settings = Settings(_env_file=None)
    notifications = AsyncMock(return_value=(3, 1))
    malware_scans = AsyncMock(return_value=(2, 0))
    retention = AsyncMock(return_value=(1, 0))
    monkeypatch.setattr(worker, "process_pending_notifications", notifications)
    monkeypatch.setattr(worker, "process_malware_scans", malware_scans)
    monkeypatch.setattr(worker, "process_retention_sweep", retention)

    outcome = await worker.process_worker_batch(session, limit=17, settings=settings)

    notifications.assert_awaited_once_with(session, limit=17)
    malware_scans.assert_awaited_once_with(session, limit=17, settings=settings)
    retention.assert_awaited_once_with(session, limit=17, settings=settings)
    assert outcome == WorkerOutcome(
        notifications_succeeded=3,
        notifications_failed=1,
        malware_scans_succeeded=2,
        malware_scans_failed=0,
        retention_sweeps_succeeded=1,
        retention_sweeps_failed=0,
    )
    assert outcome.exit_code == 1


@pytest.mark.parametrize(
    ("notifications_failed", "malware_scans_failed", "retention_sweeps_failed"),
    [(0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1)],
)
def test_worker_exit_status_includes_every_failure_class(
    notifications_failed: int,
    malware_scans_failed: int,
    retention_sweeps_failed: int,
) -> None:
    outcome = WorkerOutcome(
        notifications_succeeded=0,
        notifications_failed=notifications_failed,
        malware_scans_succeeded=0,
        malware_scans_failed=malware_scans_failed,
        retention_sweeps_succeeded=0,
        retention_sweeps_failed=retention_sweeps_failed,
    )

    expected = int(any((notifications_failed, malware_scans_failed, retention_sweeps_failed)))
    assert outcome.exit_code == expected


@pytest.mark.asyncio
async def test_failed_scan_cleanup_removes_local_quarantined_object(tmp_path: Path) -> None:
    settings = Settings(_env_file=None, internship_local_storage_path=tmp_path)
    target = tmp_path / "internships" / "student" / "upload.pdf"
    target.parent.mkdir(parents=True)
    target.write_bytes(b"quarantined")

    removed = await worker._delete_quarantined_object(settings, "internships/student/upload.pdf")

    assert removed
    assert not target.exists()


@pytest.mark.asyncio
async def test_retention_expires_and_deletes_abandoned_uploads(tmp_path: Path) -> None:
    now = datetime.now(UTC)
    upload = InternshipUpload(
        upload_id="expired-upload",
        owner_user_id=uuid.uuid4(),
        student_assignment_id=uuid.uuid4(),
        artifact_type="pdf",
        filename="report.pdf",
        content_type="application/pdf",
        size_bytes=4,
        storage_key="internships/student/expired/report.pdf",
        state="QUARANTINED",
        expires_at=now - timedelta(hours=25),
    )
    target = tmp_path / upload.storage_key
    target.parent.mkdir(parents=True)
    target.write_bytes(b"data")
    rows = MagicMock()
    rows.all.return_value = [upload]
    session = AsyncMock(spec=AsyncSession)
    session.scalars.return_value = rows
    settings = Settings(_env_file=None, internship_local_storage_path=tmp_path)

    expired = await worker._expire_abandoned_uploads(session, settings=settings, now=now, limit=10)

    assert expired == 1
    assert upload.state == "EXPIRED"
    assert upload.scan_message == "Expired by the abandoned-upload retention policy"
    assert not target.exists()


@pytest.mark.asyncio
async def test_run_returns_nonzero_for_malware_scan_failure(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    session = AsyncMock(spec=AsyncSession)
    session_context = AsyncMock()
    session_context.__aenter__.return_value = session
    outcome = WorkerOutcome(
        notifications_succeeded=4,
        notifications_failed=0,
        malware_scans_succeeded=0,
        malware_scans_failed=1,
        retention_sweeps_succeeded=1,
        retention_sweeps_failed=0,
    )
    process_batch = AsyncMock(return_value=outcome)
    recover = AsyncMock(return_value=0)
    monkeypatch.setattr(worker, "SessionFactory", lambda: session_context)
    monkeypatch.setattr(worker, "get_settings", lambda: Settings(_env_file=None))
    monkeypatch.setattr(worker, "requeue_stale_running_events", recover)
    monkeypatch.setattr(worker, "process_worker_batch", process_batch)

    exit_code = await worker.run(limit=9)

    assert exit_code == 1
    process_batch.assert_awaited_once()
    assert "malware scans: 0 succeeded, 1 failed" in capsys.readouterr().out


@pytest.mark.asyncio
async def test_stale_running_claim_is_requeued_with_failed_attempt() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    now = datetime.now(UTC)
    async with factory() as session:
        event = OutboxEvent(
            event_type="NotificationRequested",
            aggregate_type="test",
            aggregate_id=uuid.uuid4(),
            payload={},
            status="RUNNING",
            attempts=1,
            available_at=now - timedelta(hours=1),
        )
        event.updated_at = now - timedelta(hours=1)
        session.add(event)
        await session.flush()
        attempt = JobAttempt(
            outbox_event_id=event.id,
            attempt_number=1,
            status="RUNNING",
            started_at=now - timedelta(hours=1),
        )
        session.add(attempt)
        await session.commit()

        recovered = await worker.requeue_stale_running_events(
            session,
            stale_after=timedelta(minutes=35),
            now=now,
        )

        await session.refresh(event)
        await session.refresh(attempt)
        assert recovered == 1
        assert event.status == "PENDING"
        assert event.available_at.replace(tzinfo=UTC) == now
        assert attempt.status == "FAILED"
        assert attempt.error_category == "StaleWorkerClaim"
        assert attempt.finished_at is not None
        assert attempt.finished_at.replace(tzinfo=UTC) == now
    await engine.dispose()
