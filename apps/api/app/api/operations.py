import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import select

from app.auth.dependencies import DbSession, IdempotencyKey, require_roles
from app.auth.service import SessionPrincipal
from app.config import Settings, get_settings
from app.domain.enums import Role
from app.domain.models import OutboxEvent
from app.domain.schemas import (
    AgentRunView,
    DashboardSummary,
    DeadLetterRecoveryRequest,
    IntegrationStatus,
    OperationsJobView,
    ProviderSynchronizationView,
)
from app.operations.service import (
    OperationsConflict,
    OperationsNotFound,
    agent_timeline,
    audit_timeline,
    dashboard_summary,
    integration_health,
    list_jobs,
    provider_sync_timeline,
    recover_dead_letter,
)
from app.outbox.cloud_tasks import CloudTaskPayload
from app.outbox.task_auth import verify_cloud_task_identity

router = APIRouter(prefix="/ops", tags=["operations"])
OperationsPrincipal = Annotated[
    SessionPrincipal, Depends(require_roles(Role.COORDINATOR, Role.PLATFORM_ADMIN))
]


@router.post("/tasks/process-outbox")
async def process_outbox_task(
    body: CloudTaskPayload,
    request: Request,
    session: DbSession,
    settings: Annotated[Settings, Depends(get_settings)],
) -> dict[str, str]:
    verify_cloud_task_identity(request, settings)
    event = await session.scalar(select(OutboxEvent).where(OutboxEvent.id == body.outbox_event_id))
    if event is None or event.event_type != body.event_type:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Outbox event not found")
    if event.correlation_id is not None and event.correlation_id != body.correlation_id:
        raise HTTPException(status.HTTP_409_CONFLICT, "Outbox correlation does not match")
    # The task carries no domain payload. The worker loads it from the committed
    # outbox row, so retries cannot mutate or leak a copied task body.
    if event.event_type != "NotificationRequested":
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "No hosted handler is registered for this outbox event type",
        )
    from app.notifications.service import process_notification_event

    processed = await process_notification_event(session, event_id=event.id)
    return {"status": processed.status, "outbox_event_id": str(processed.id)}


@router.get("/dashboard", response_model=DashboardSummary)
async def dashboard(
    principal: OperationsPrincipal,
    session: DbSession,
    settings: Annotated[Settings, Depends(get_settings)],
) -> DashboardSummary:
    return await dashboard_summary(session, settings=settings)


@router.get("/jobs", response_model=list[OperationsJobView])
async def jobs(
    principal: OperationsPrincipal,
    session: DbSession,
    job_status: Annotated[str | None, Query(alias="status", max_length=30)] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
) -> list[OperationsJobView]:
    return await list_jobs(session, status=job_status, limit=limit)


@router.post("/jobs/{event_id}/recover", response_model=OperationsJobView)
async def recover_job(
    event_id: uuid.UUID,
    body: DeadLetterRecoveryRequest,
    principal: OperationsPrincipal,
    session: DbSession,
    idempotency_key: IdempotencyKey,
    request: Request,
) -> OperationsJobView:
    try:
        event = await recover_dead_letter(
            session,
            principal=principal,
            event_id=event_id,
            reason=body.reason,
            idempotency_key=idempotency_key,
            correlation_id=request.state.correlation_id,
        )
    except OperationsNotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except OperationsConflict as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
    rows = await list_jobs(session, status=None, limit=200)
    return next(item for item in rows if item.id == event.id)


@router.get("/integrations", response_model=list[IntegrationStatus])
async def integrations(
    principal: OperationsPrincipal,
    session: DbSession,
    settings: Annotated[Settings, Depends(get_settings)],
) -> list[IntegrationStatus]:
    return await integration_health(session, settings=settings)


@router.get("/provider-synchronizations", response_model=list[ProviderSynchronizationView])
async def provider_synchronizations(
    principal: OperationsPrincipal,
    session: DbSession,
    provider: Annotated[str | None, Query(max_length=60)] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
) -> list[ProviderSynchronizationView]:
    return await provider_sync_timeline(session, provider=provider, limit=limit)


@router.get("/agent-runs", response_model=list[AgentRunView])
async def agent_runs(
    principal: OperationsPrincipal,
    session: DbSession,
    project_id: uuid.UUID | None = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
) -> list[AgentRunView]:
    rows = await agent_timeline(session, project_id=project_id, limit=limit)
    return [AgentRunView.model_validate(row) for row in rows]


@router.get("/audit-events")
async def audit_events(
    principal: OperationsPrincipal,
    session: DbSession,
    resource_id: uuid.UUID | None = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
) -> list[dict[str, object]]:
    rows = await audit_timeline(session, resource_id=resource_id, limit=limit)
    return [
        {
            "id": row.id,
            "actor_id": row.actor_id,
            "organization_id": row.organization_id,
            "action": row.action,
            "resource_type": row.resource_type,
            "resource_id": row.resource_id,
            "correlation_id": row.correlation_id,
            "payload": row.payload,
            "created_at": row.created_at,
        }
        for row in rows
    ]
