import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.service import SessionPrincipal
from app.config import Settings
from app.domain.models import (
    AgentRun,
    Approval,
    AuditEvent,
    JobAttempt,
    OutboxEvent,
    OutboxRecovery,
    PaymentEvent,
    Project,
    ProviderSynchronization,
)
from app.domain.schemas import (
    DashboardSummary,
    IntegrationStatus,
    JobAttemptView,
    OperationsJobView,
    ProviderSynchronizationView,
)


class OperationsError(ValueError):
    pass


class OperationsNotFound(OperationsError):
    pass


class OperationsConflict(OperationsError):
    pass


async def dashboard_summary(session: AsyncSession, *, settings: Settings) -> DashboardSummary:
    state_rows = (
        await session.execute(select(Project.state, func.count(Project.id)).group_by(Project.state))
    ).all()
    pending = await session.scalar(
        select(func.count(Approval.id)).where(Approval.decision == "PENDING")
    )
    failed_runs = await session.scalar(
        select(func.count(AgentRun.id)).where(AgentRun.status == "FAILED")
    )
    dead_letters = await session.scalar(
        select(func.count(OutboxEvent.id)).where(OutboxEvent.status == "DEAD_LETTER")
    )
    payment_exceptions = await session.scalar(
        select(func.count(PaymentEvent.id)).where(PaymentEvent.event_type.like("%failed%"))
    )
    return DashboardSummary(
        environment_label="demo" if settings.demo_mode else settings.app_env,
        is_demo=settings.demo_mode,
        projects_by_state={state: count for state, count in state_rows},
        pending_approvals=pending or 0,
        failed_agent_runs=failed_runs or 0,
        dead_letter_jobs=dead_letters or 0,
        payment_exceptions=payment_exceptions or 0,
    )


async def list_jobs(
    session: AsyncSession, *, status: str | None = None, limit: int = 100
) -> list[OperationsJobView]:
    query = select(OutboxEvent).order_by(OutboxEvent.created_at.desc()).limit(limit)
    if status is not None:
        query = query.where(OutboxEvent.status == status)
    events = list((await session.scalars(query)).all())
    if not events:
        return []
    attempt_rows = list(
        (
            await session.scalars(
                select(JobAttempt)
                .where(JobAttempt.outbox_event_id.in_([event.id for event in events]))
                .order_by(JobAttempt.outbox_event_id, JobAttempt.attempt_number)
            )
        ).all()
    )
    attempts_by_event: dict[uuid.UUID, list[JobAttemptView]] = {}
    for attempt in attempt_rows:
        attempts_by_event.setdefault(attempt.outbox_event_id, []).append(
            JobAttemptView.model_validate(attempt)
        )
    return [
        OperationsJobView(
            id=event.id,
            event_type=event.event_type,
            aggregate_type=event.aggregate_type,
            aggregate_id=event.aggregate_id,
            status=event.status,
            attempts=event.attempts,
            available_at=event.available_at,
            last_error=event.last_error,
            attempt_history=attempts_by_event.get(event.id, []),
        )
        for event in events
    ]


async def recover_dead_letter(
    session: AsyncSession,
    *,
    principal: SessionPrincipal,
    event_id: uuid.UUID,
    reason: str,
    idempotency_key: str,
    correlation_id: uuid.UUID,
) -> OutboxEvent:
    existing = await session.scalar(
        select(OutboxRecovery).where(OutboxRecovery.idempotency_key == idempotency_key)
    )
    if existing is not None:
        if existing.outbox_event_id != event_id:
            raise OperationsConflict("Idempotency key belongs to a different job")
        event: OutboxEvent | None = await session.scalar(
            select(OutboxEvent).where(OutboxEvent.id == event_id)
        )
        if event is None:
            raise OperationsNotFound("Job not found")
        return event

    event = await session.scalar(
        select(OutboxEvent).where(OutboxEvent.id == event_id).with_for_update()
    )
    if event is None:
        raise OperationsNotFound("Job not found")
    if event.status != "DEAD_LETTER":
        raise OperationsConflict("Only dead-letter jobs can be recovered")

    now = datetime.now(UTC)
    event.status = "PENDING"
    event.available_at = now
    event.last_error = None
    recovery = OutboxRecovery(
        outbox_event_id=event.id,
        recovered_by_id=principal.user_id,
        reason=reason,
        idempotency_key=idempotency_key,
        recovered_at=now,
    )
    session.add_all(
        [
            recovery,
            AuditEvent(
                actor_id=principal.user_id,
                organization_id=principal.organization_id,
                action="outbox.recovered",
                resource_type="outbox_event",
                resource_id=event.id,
                correlation_id=correlation_id,
                payload={"reason": reason, "previous_attempts": event.attempts},
            ),
        ]
    )
    await session.commit()
    await session.refresh(event)
    return event


async def integration_inventory(
    session: AsyncSession, *, settings: Settings
) -> list[IntegrationStatus]:
    sync_rows = list(
        (
            await session.scalars(
                select(ProviderSynchronization).order_by(ProviderSynchronization.checked_at.desc())
            )
        ).all()
    )
    latest = {row.provider: row for row in reversed(sync_rows)}
    configured = [
        IntegrationStatus(
            provider="database",
            mode=settings.database_pool_mode,
            configured=bool(settings.database_url),
            live_side_effects_enabled=True,
        ),
        IntegrationStatus(
            provider="identity",
            mode=settings.identity_provider,
            configured=(
                settings.identity_provider == "local"
                or bool(
                    settings.supabase_url
                    and (settings.supabase_publishable_key or settings.supabase_anon_key)
                )
            ),
            live_side_effects_enabled=settings.identity_provider == "supabase",
        ),
        IntegrationStatus(
            provider="ai",
            mode=settings.gemini_provider,
            configured=(
                settings.gemini_provider in {"disabled", "fixture"}
                or bool(settings.google_cloud_project or settings.gemini_api_key)
            ),
            live_side_effects_enabled=settings.gemini_provider == "gemini",
        ),
        IntegrationStatus(
            provider="object_storage",
            mode=settings.storage_provider,
            configured=(
                settings.storage_provider == "local"
                or (
                    settings.storage_provider == "supabase"
                    and bool(
                        settings.supabase_url
                        and settings.supabase_service_role_key
                        and settings.supabase_storage_bucket
                    )
                )
                or (settings.storage_provider == "gcs" and bool(settings.cloud_storage_bucket))
            ),
            live_side_effects_enabled=settings.storage_provider in {"supabase", "gcs"},
        ),
        IntegrationStatus(
            provider="malware_scanner",
            mode=settings.upload_scanner_provider,
            configured=(
                settings.upload_scanner_provider == "disabled" or bool(settings.clamav_host)
            ),
            live_side_effects_enabled=settings.upload_scanner_provider == "clamav",
        ),
        IntegrationStatus(
            provider="payments",
            mode=settings.payment_provider,
            configured=True,
            live_side_effects_enabled=False,
        ),
        IntegrationStatus(
            provider="credential_signing",
            mode=settings.credential_signing_provider,
            configured=(
                settings.credential_signing_provider == "demo"
                or bool(settings.credential_kms_key_name)
            ),
            live_side_effects_enabled=settings.credential_signing_provider == "kms",
        ),
        IntegrationStatus(
            provider="in_app_notifications",
            mode="database",
            configured=True,
            live_side_effects_enabled=False,
        ),
    ]
    return [
        item.model_copy(
            update={
                "last_sync_status": latest[item.provider].status,
                "last_synced_at": latest[item.provider].checked_at,
                "last_error_category": latest[item.provider].error_category,
            }
        )
        if item.provider in latest
        else item
        for item in configured
    ]


async def provider_sync_timeline(
    session: AsyncSession, *, provider: str | None, limit: int = 100
) -> list[ProviderSynchronizationView]:
    query = (
        select(ProviderSynchronization)
        .order_by(ProviderSynchronization.checked_at.desc())
        .limit(limit)
    )
    if provider is not None:
        query = query.where(ProviderSynchronization.provider == provider)
    rows = list((await session.scalars(query)).all())
    return [ProviderSynchronizationView.model_validate(row) for row in rows]


async def agent_timeline(
    session: AsyncSession, *, project_id: uuid.UUID | None, limit: int = 100
) -> list[AgentRun]:
    query = select(AgentRun).order_by(AgentRun.created_at.desc()).limit(limit)
    if project_id is not None:
        query = query.where(AgentRun.project_id == project_id)
    return list((await session.scalars(query)).all())


async def audit_timeline(
    session: AsyncSession, *, resource_id: uuid.UUID | None, limit: int = 100
) -> list[AuditEvent]:
    query = select(AuditEvent).order_by(AuditEvent.created_at.desc()).limit(limit)
    if resource_id is not None:
        query = query.where(AuditEvent.resource_id == resource_id)
    return list((await session.scalars(query)).all())
