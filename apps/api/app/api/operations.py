import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.auth.dependencies import DbSession, IdempotencyKey, require_roles
from app.auth.service import SessionPrincipal
from app.config import Settings, get_settings
from app.domain.enums import Role
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
    integration_inventory,
    list_jobs,
    provider_sync_timeline,
    recover_dead_letter,
)

router = APIRouter(prefix="/ops", tags=["operations"])
OperationsPrincipal = Annotated[
    SessionPrincipal, Depends(require_roles(Role.COORDINATOR, Role.PLATFORM_ADMIN))
]


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
    return await integration_inventory(session, settings=settings)


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
