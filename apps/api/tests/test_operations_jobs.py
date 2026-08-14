import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.auth.service import SessionPrincipal
from app.domain.models import Base, JobAttempt, Organization, OutboxEvent, OutboxRecovery, User
from app.operations.service import recover_dead_letter
from app.outbox.service import OutboxEventAlreadyRunning, OutboxEventNotProcessable, process_one


@pytest.mark.asyncio
async def test_job_attempts_redact_secrets_and_recovery_is_idempotent() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    async with factory() as session:
        organization = Organization(name="Ops", slug="job-ops", kind="platform")
        operator = User(email="operator@example.test", display_name="Operator")
        session.add_all([organization, operator])
        await session.flush()
        event = OutboxEvent(
            event_type="FailingJob",
            aggregate_type="test",
            aggregate_id=uuid.uuid4(),
            payload={},
            available_at=datetime.now(UTC),
        )
        session.add(event)
        await session.commit()

        async def failing_handler(payload: dict[str, object]) -> None:
            raise RuntimeError("token=private-value request failed")

        with pytest.raises(RuntimeError):
            await process_one(
                session,
                handlers={"FailingJob": failing_handler},
                event_id=event.id,
                max_attempts=1,
            )
        await session.refresh(event)
        attempt = await session.scalar(
            select(JobAttempt).where(JobAttempt.outbox_event_id == event.id)
        )
        assert event.status == "DEAD_LETTER"
        assert attempt is not None and attempt.status == "FAILED"
        assert "private-value" not in (attempt.error_message or "")
        assert "[REDACTED]" in (attempt.error_message or "")

        principal = SessionPrincipal(
            user_id=operator.id,
            organization_id=organization.id,
            role="coordinator",
        )
        first = await recover_dead_letter(
            session,
            principal=principal,
            event_id=event.id,
            reason="Operator confirmed the provider incident has been resolved.",
            idempotency_key="recover-job-once",
            correlation_id=uuid.uuid4(),
        )
        second = await recover_dead_letter(
            session,
            principal=principal,
            event_id=event.id,
            reason="Operator confirmed the provider incident has been resolved.",
            idempotency_key="recover-job-once",
            correlation_id=uuid.uuid4(),
        )
        recovery_count = await session.scalar(select(func.count(OutboxRecovery.id)))
        assert first.id == second.id == event.id
        assert second.status == "PENDING"
        assert recovery_count == 1
    await engine.dispose()


@pytest.mark.asyncio
async def test_process_one_rejects_running_and_dead_letter_claims() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    async with factory() as session:
        running = OutboxEvent(
            event_type="ClaimedJob",
            aggregate_type="test",
            aggregate_id=uuid.uuid4(),
            payload={},
            status="RUNNING",
            available_at=datetime.now(UTC),
        )
        dead_letter = OutboxEvent(
            event_type="ClaimedJob",
            aggregate_type="test",
            aggregate_id=uuid.uuid4(),
            payload={},
            status="DEAD_LETTER",
            available_at=datetime.now(UTC),
        )
        session.add_all([running, dead_letter])
        await session.commit()

        async def handler(_: dict[str, object]) -> None:
            raise AssertionError("a claimed event must not execute")

        with pytest.raises(OutboxEventAlreadyRunning):
            await process_one(
                session,
                handlers={"ClaimedJob": handler},
                event_id=running.id,
            )
        with pytest.raises(OutboxEventNotProcessable):
            await process_one(
                session,
                handlers={"ClaimedJob": handler},
                event_id=dead_letter.id,
            )
    await engine.dispose()


@pytest.mark.asyncio
async def test_process_one_rolls_back_partial_handler_changes_before_recording_failure() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    async with factory() as session:
        event = OutboxEvent(
            event_type="FailingJob",
            aggregate_type="test",
            aggregate_id=uuid.uuid4(),
            payload={"state": "original"},
            available_at=datetime.now(UTC),
        )
        session.add(event)
        await session.commit()

        async def failing_handler(_: dict[str, object]) -> None:
            claimed = await session.get(OutboxEvent, event.id)
            assert claimed is not None
            claimed.payload = {"state": "partial"}
            await session.flush()
            raise RuntimeError("handler failed after a partial database write")

        with pytest.raises(RuntimeError):
            await process_one(
                session,
                handlers={"FailingJob": failing_handler},
                event_id=event.id,
            )

        await session.refresh(event)
        attempt = await session.scalar(
            select(JobAttempt).where(JobAttempt.outbox_event_id == event.id)
        )
        assert event.payload == {"state": "original"}
        assert event.status == "PENDING"
        assert attempt is not None and attempt.status == "FAILED"
    await engine.dispose()


@pytest.mark.asyncio
async def test_process_one_recovers_failed_database_transaction() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    async with factory() as session:
        event = OutboxEvent(
            event_type="ConstraintFailure",
            aggregate_type="test",
            aggregate_id=uuid.uuid4(),
            payload={},
            available_at=datetime.now(UTC),
        )
        session.add(event)
        await session.commit()

        async def violating_handler(_: dict[str, object]) -> None:
            session.add(
                JobAttempt(
                    outbox_event_id=event.id,
                    attempt_number=1,
                    status="RUNNING",
                    started_at=datetime.now(UTC),
                )
            )
            await session.flush()

        with pytest.raises(IntegrityError):
            await process_one(
                session,
                handlers={"ConstraintFailure": violating_handler},
                event_id=event.id,
            )

        await session.refresh(event)
        attempt = await session.scalar(
            select(JobAttempt).where(JobAttempt.outbox_event_id == event.id)
        )
        assert event.status == "PENDING"
        assert attempt is not None and attempt.status == "FAILED"
        assert attempt.error_category == "IntegrityError"
    await engine.dispose()
