import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.auth.service import SessionPrincipal
from app.domain.models import Base, JobAttempt, Organization, OutboxEvent, OutboxRecovery, User
from app.operations.service import recover_dead_letter
from app.outbox.service import process_one


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
