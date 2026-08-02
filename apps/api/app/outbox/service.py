import re
import uuid
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import JobAttempt, OutboxEvent

EventHandler = Callable[[dict[str, object]], Awaitable[None]]


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
        select(OutboxEvent).where(OutboxEvent.id == event_id).with_for_update()
    )
    if event is None:
        raise ValueError("Outbox event not found")
    if event.status == "SUCCEEDED":
        return event
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
    try:
        await handler(event.payload)
    except Exception as exc:
        event.status = "DEAD_LETTER" if event.attempts >= max_attempts else "PENDING"
        event.last_error = _safe_error(exc)
        event.available_at = datetime.now(UTC) + timedelta(seconds=min(300, 2**event.attempts))
        attempt.status = "FAILED"
        attempt.finished_at = datetime.now(UTC)
        attempt.error_category = type(exc).__name__[:100]
        attempt.error_message = event.last_error
        await session.commit()
        raise
    event.status = "SUCCEEDED"
    event.last_error = None
    attempt.status = "SUCCEEDED"
    attempt.finished_at = datetime.now(UTC)
    await session.commit()
    return event
