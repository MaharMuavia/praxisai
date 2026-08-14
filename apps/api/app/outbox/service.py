import re
import uuid
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import JobAttempt, OutboxEvent

EventHandler = Callable[[dict[str, object]], Awaitable[None]]


class OutboxEventAlreadyRunning(RuntimeError):
    """Raised when another worker owns an outbox event claim."""


class OutboxEventNotProcessable(RuntimeError):
    """Raised when an event must be recovered before it can run again."""


def _utc(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def _safe_error(exc: Exception) -> str:
    message = str(exc)[:2_000]
    return re.sub(
        r"(?i)(api[_-]?key|token|authorization|secret|password)(\s*[:=]\s*)\S+",
        r"\1\2[REDACTED]",
        message,
    )


async def process_one(
    session: AsyncSession,
    *,
    handlers: dict[str, EventHandler],
    event_id: uuid.UUID,
    max_attempts: int = 5,
) -> OutboxEvent:
    event = await session.scalar(
        select(OutboxEvent)
        .where(OutboxEvent.id == event_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    if event is None:
        raise ValueError("Outbox event not found")
    if event.status == "SUCCEEDED":
        return event
    if event.status == "RUNNING":
        raise OutboxEventAlreadyRunning("Outbox event is already claimed")
    if event.status != "PENDING":
        raise OutboxEventNotProcessable("Outbox event must be recovered before processing")
    if _utc(event.available_at) > datetime.now(UTC):
        raise ValueError("Outbox event is not available yet")
    handler = handlers.get(event.event_type)
    if handler is None:
        raise ValueError(f"No handler is registered for {event.event_type}")
    event.status = "RUNNING"
    event.attempts += 1
    attempt = JobAttempt(
        outbox_event_id=event.id,
        attempt_number=event.attempts,
        status="RUNNING",
        started_at=datetime.now(UTC),
    )
    session.add(attempt)
    await session.commit()
    attempt_id = attempt.id
    try:
        await handler(event.payload)
    except Exception as exc:
        error_message = _safe_error(exc)
        error_category = type(exc).__name__[:100]
        await session.rollback()
        event = await session.scalar(
            select(OutboxEvent)
            .where(OutboxEvent.id == event_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
        recorded_attempt = await session.get(JobAttempt, attempt_id, populate_existing=True)
        if event is None or recorded_attempt is None:
            await session.rollback()
            raise RuntimeError("Outbox failure state could not be recovered") from exc
        event.status = "DEAD_LETTER" if event.attempts >= max_attempts else "PENDING"
        event.last_error = error_message
        event.available_at = datetime.now(UTC) + timedelta(seconds=min(300, 2**event.attempts))
        recorded_attempt.status = "FAILED"
        recorded_attempt.finished_at = datetime.now(UTC)
        recorded_attempt.error_category = error_category
        recorded_attempt.error_message = event.last_error
        await session.commit()
        raise
    event.status = "SUCCEEDED"
    event.last_error = None
    attempt.status = "SUCCEEDED"
    attempt.finished_at = datetime.now(UTC)
    await session.commit()
    return event
