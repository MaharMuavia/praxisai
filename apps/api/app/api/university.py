from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.auth.dependencies import DbSession, IdempotencyKey, require_roles
from app.auth.service import SessionPrincipal
from app.config import Settings, get_settings
from app.domain.enums import Role
from app.domain.schemas import UniversityExportRequest, UniversityExportView, UniversityMetrics
from app.university.service import (
    UniversityAccessError,
    UniversityConflict,
    aggregate_metrics,
    list_exports,
    request_export,
)

router = APIRouter(prefix="/university", tags=["university"])
UniversityPrincipal = Annotated[SessionPrincipal, Depends(require_roles(Role.UNIVERSITY_VIEWER))]


@router.get("/metrics", response_model=UniversityMetrics)
async def metrics(
    principal: UniversityPrincipal,
    session: DbSession,
    settings: Annotated[Settings, Depends(get_settings)],
) -> UniversityMetrics:
    try:
        return await aggregate_metrics(session, principal=principal, settings=settings)
    except UniversityAccessError as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN, str(exc)) from exc


@router.get("/exports", response_model=list[UniversityExportView])
async def exports(principal: UniversityPrincipal, session: DbSession) -> list[UniversityExportView]:
    try:
        rows = await list_exports(session, principal=principal)
    except UniversityAccessError as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN, str(exc)) from exc
    return [UniversityExportView.model_validate(row) for row in rows]


@router.post("/exports", response_model=UniversityExportView, status_code=201)
async def create_export(
    body: UniversityExportRequest,
    principal: UniversityPrincipal,
    session: DbSession,
    idempotency_key: IdempotencyKey,
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
) -> UniversityExportView:
    try:
        row = await request_export(
            session,
            principal=principal,
            purpose=body.purpose,
            idempotency_key=idempotency_key,
            correlation_id=request.state.correlation_id,
            settings=settings,
        )
    except UniversityConflict as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
    except UniversityAccessError as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN, str(exc)) from exc
    return UniversityExportView.model_validate(row)
