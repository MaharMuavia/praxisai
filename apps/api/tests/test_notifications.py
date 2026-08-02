import uuid

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.auth.service import SessionPrincipal
from app.domain.models import (
    AuditEvent,
    Base,
    Notification,
    Organization,
    OutboxEvent,
    ProviderSynchronization,
    User,
)
from app.domain.schemas import NotificationPreferenceUpdate
from app.notifications.service import (
    NotificationConflict,
    list_preferences,
    notification_event,
    process_notification_event,
    update_preference,
)


@pytest.mark.asyncio
async def test_preferences_suppress_optional_delivery_but_preserve_critical_delivery() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    async with factory() as session:
        organization = Organization(name="Test Ops", slug="notification-ops", kind="platform")
        user = User(email="notify@example.test", display_name="Notification User")
        session.add_all([organization, user])
        await session.commit()
        principal = SessionPrincipal(user.id, organization.id, "student")

        defaults = await list_preferences(session, user_id=user.id)
        assert len(defaults) == 6
        assert all(item.enabled for item in defaults)
        disabled = await update_preference(
            session,
            principal=principal,
            update=NotificationPreferenceUpdate(category="projects", enabled=False),
            correlation_id=uuid.uuid4(),
        )
        assert disabled.enabled is False
        assert await session.scalar(select(func.count(AuditEvent.id))) == 1
        with pytest.raises(NotificationConflict):
            await update_preference(
                session,
                principal=principal,
                update=NotificationPreferenceUpdate(category="payments", enabled=False),
                correlation_id=uuid.uuid4(),
            )

        optional_event = notification_event(
            recipient_user_id=user.id,
            category="projects",
            title="Project changed",
            body="The project moved to client review.",
            resource_path="/student/projects/example",
            correlation_id=uuid.uuid4(),
        )
        critical_event = notification_event(
            recipient_user_id=user.id,
            category="payments",
            title="Payout approved",
            body="Your payout allocation was approved.",
            resource_path="/student/earnings",
            correlation_id=uuid.uuid4(),
        )
        session.add_all([optional_event, critical_event])
        await session.commit()

        skipped = await process_notification_event(session, event_id=optional_event.id)
        delivered = await process_notification_event(session, event_id=critical_event.id)
        repeated = await process_notification_event(session, event_id=critical_event.id)

        notifications = list((await session.scalars(select(Notification))).all())
        synchronizations = list((await session.scalars(select(ProviderSynchronization))).all())
        assert skipped.status == "SUCCEEDED"
        assert delivered.status == repeated.status == "SUCCEEDED"
        assert len(notifications) == 1
        assert notifications[0].kind == "payments"
        assert notifications[0].source_outbox_event_id == critical_event.id
        assert {item.status for item in synchronizations} == {"SKIPPED", "SUCCEEDED"}
        assert await session.scalar(select(func.count(OutboxEvent.id))) == 2
    await engine.dispose()
