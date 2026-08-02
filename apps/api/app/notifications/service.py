import uuid
from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.service import SessionPrincipal
from app.domain.models import (
    AuditEvent,
    Notification,
    NotificationPreference,
    OutboxEvent,
    ProviderSynchronization,
    User,
)
from app.domain.schemas import (
    NotificationCategory,
    NotificationPreferenceUpdate,
    NotificationPreferenceView,
)
from app.outbox.service import process_one

CATEGORIES: tuple[NotificationCategory, ...] = (
    "projects",
    "offers",
    "payments",
    "credentials",
    "appeals",
    "operations",
)
CRITICAL_CATEGORIES: frozenset[NotificationCategory] = frozenset(
    {"payments", "credentials", "appeals"}
)


class NotificationError(ValueError):
    pass


class NotificationNotFound(NotificationError):
    pass


class NotificationConflict(NotificationError):
    pass


class NotificationPayload(BaseModel):
    recipient_user_id: uuid.UUID
    category: NotificationCategory
    title: str = Field(min_length=3, max_length=160)
    body: str = Field(min_length=3, max_length=4_000)
    resource_path: str | None = Field(default=None, pattern=r"^/", max_length=500)
    correlation_id: uuid.UUID


def notification_event(
    *,
    recipient_user_id: uuid.UUID,
    category: NotificationCategory,
    title: str,
    body: str,
    resource_path: str | None,
    correlation_id: uuid.UUID,
) -> OutboxEvent:
    payload = NotificationPayload(
        recipient_user_id=recipient_user_id,
        category=category,
        title=title,
        body=body,
        resource_path=resource_path,
        correlation_id=correlation_id,
    )
    return OutboxEvent(
        event_type="NotificationRequested",
        aggregate_type="user",
        aggregate_id=recipient_user_id,
        payload=payload.model_dump(mode="json"),
    )


async def list_preferences(
    session: AsyncSession, *, user_id: uuid.UUID
) -> list[NotificationPreferenceView]:
    rows = list(
        (
            await session.scalars(
                select(NotificationPreference).where(NotificationPreference.user_id == user_id)
            )
        ).all()
    )
    configured = {row.category: row.enabled for row in rows}
    return [
        NotificationPreferenceView(category=category, enabled=configured.get(category, True))
        for category in CATEGORIES
    ]


async def update_preference(
    session: AsyncSession,
    *,
    principal: SessionPrincipal,
    update: NotificationPreferenceUpdate,
    correlation_id: uuid.UUID,
) -> NotificationPreferenceView:
    if update.category in CRITICAL_CATEGORIES and not update.enabled:
        raise NotificationConflict(
            "Critical payment, credential, and appeal notifications cannot be disabled"
        )
    user = await session.scalar(select(User).where(User.id == principal.user_id).with_for_update())
    if user is None:
        raise NotificationNotFound("User not found")
    preference = await session.scalar(
        select(NotificationPreference).where(
            NotificationPreference.user_id == principal.user_id,
            NotificationPreference.category == update.category,
        )
    )
    previous = True if preference is None else preference.enabled
    if preference is None:
        preference = NotificationPreference(
            user_id=principal.user_id,
            category=update.category,
            enabled=update.enabled,
        )
        session.add(preference)
    else:
        preference.enabled = update.enabled
    session.add(
        AuditEvent(
            actor_id=principal.user_id,
            organization_id=principal.organization_id,
            action="notification_preference.updated",
            resource_type="user",
            resource_id=principal.user_id,
            correlation_id=correlation_id,
            payload={
                "category": update.category,
                "previous_enabled": previous,
                "enabled": update.enabled,
            },
        )
    )
    await session.commit()
    return NotificationPreferenceView(category=update.category, enabled=update.enabled)


async def list_user_notifications(
    session: AsyncSession, *, user_id: uuid.UUID, limit: int = 100
) -> list[Notification]:
    return list(
        (
            await session.scalars(
                select(Notification)
                .where(Notification.user_id == user_id)
                .order_by(Notification.created_at.desc())
                .limit(limit)
            )
        ).all()
    )


async def mark_notification_read(
    session: AsyncSession, *, user_id: uuid.UUID, notification_id: uuid.UUID
) -> None:
    notification = await session.scalar(
        select(Notification).where(Notification.id == notification_id).with_for_update()
    )
    if notification is None or notification.user_id != user_id:
        raise NotificationNotFound("Notification not found")
    if notification.read_at is None:
        notification.read_at = datetime.now(UTC)
        await session.commit()


async def _deliver_in_app(
    session: AsyncSession, *, event: OutboxEvent, raw_payload: dict[str, object]
) -> None:
    try:
        payload = NotificationPayload.model_validate(raw_payload)
        existing = await session.scalar(
            select(Notification).where(
                Notification.user_id == payload.recipient_user_id,
                Notification.source_outbox_event_id == event.id,
            )
        )
        if existing is not None:
            return
        preference = await session.scalar(
            select(NotificationPreference).where(
                NotificationPreference.user_id == payload.recipient_user_id,
                NotificationPreference.category == payload.category,
            )
        )
        enabled = (
            preference is None or preference.enabled or payload.category in CRITICAL_CATEGORIES
        )
        status: Literal["SUCCEEDED", "SKIPPED"] = "SUCCEEDED" if enabled else "SKIPPED"
        if enabled:
            session.add(
                Notification(
                    user_id=payload.recipient_user_id,
                    kind=payload.category,
                    title=payload.title,
                    body=payload.body,
                    resource_path=payload.resource_path,
                    source_outbox_event_id=event.id,
                )
            )
        session.add(
            ProviderSynchronization(
                provider="in_app_notifications",
                operation="deliver",
                mode="database",
                status=status,
                resource_type="outbox_event",
                resource_id=event.id,
                correlation_id=payload.correlation_id,
                error_category=None,
                details={"category": payload.category, "delivery_created": enabled},
                checked_at=datetime.now(UTC),
            )
        )
    except Exception as exc:
        session.add(
            ProviderSynchronization(
                provider="in_app_notifications",
                operation="deliver",
                mode="database",
                status="FAILED",
                resource_type="outbox_event",
                resource_id=event.id,
                correlation_id=uuid.uuid4(),
                error_category=type(exc).__name__[:100],
                details={},
                checked_at=datetime.now(UTC),
            )
        )
        raise


async def process_notification_event(
    session: AsyncSession, *, event_id: uuid.UUID, max_attempts: int = 5
) -> OutboxEvent:
    event = await session.scalar(select(OutboxEvent).where(OutboxEvent.id == event_id))
    if event is None:
        raise NotificationNotFound("Outbox event not found")
    if event.event_type != "NotificationRequested":
        raise NotificationConflict("The event is not a notification delivery job")

    async def handler(payload: dict[str, object]) -> None:
        await _deliver_in_app(session, event=event, raw_payload=payload)

    return await process_one(
        session,
        handlers={"NotificationRequested": handler},
        event_id=event_id,
        max_attempts=max_attempts,
    )


async def process_pending_notifications(
    session: AsyncSession, *, limit: int = 100, max_attempts: int = 5
) -> tuple[int, int]:
    now = datetime.now(UTC)
    event_ids = list(
        (
            await session.scalars(
                select(OutboxEvent.id)
                .where(
                    OutboxEvent.event_type == "NotificationRequested",
                    OutboxEvent.status == "PENDING",
                    OutboxEvent.available_at <= now,
                )
                .order_by(OutboxEvent.created_at)
                .limit(limit)
            )
        ).all()
    )
    succeeded = 0
    failed = 0
    for event_id in event_ids:
        try:
            await process_notification_event(session, event_id=event_id, max_attempts=max_attempts)
            succeeded += 1
        except Exception:
            failed += 1
    return succeeded, failed
