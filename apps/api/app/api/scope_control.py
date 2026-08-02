import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.dependencies import DbSession, Principal, require_roles
from app.auth.service import SessionPrincipal
from app.change_orders.service import (
    ScopeControlDenied,
    ScopeControlError,
    ScopeControlNotFound,
    create_change_order,
    decide_change_order,
    list_change_orders,
    list_scope_changes,
    request_scope_change,
)
from app.domain.enums import Role
from app.domain.models import ChangeOrder, ScopeChangeRequest
from app.domain.schemas import (
    ChangeOrderCreate,
    ChangeOrderDecision,
    ChangeOrderView,
    ScopeChangeCreate,
    ScopeChangeView,
)

router = APIRouter(tags=["scope control"])


def _http_error(exc: ScopeControlError) -> HTTPException:
    if isinstance(exc, ScopeControlNotFound):
        return HTTPException(status.HTTP_404_NOT_FOUND, str(exc))
    if isinstance(exc, ScopeControlDenied):
        return HTTPException(status.HTTP_403_FORBIDDEN, str(exc))
    return HTTPException(status.HTTP_409_CONFLICT, str(exc))


@router.get(
    "/projects/{project_id}/scope-change-requests",
    response_model=list[ScopeChangeView],
)
async def get_scope_change_requests(
    project_id: uuid.UUID, principal: Principal, session: DbSession
) -> list[ScopeChangeRequest]:
    try:
        return await list_scope_changes(session, project_id=project_id, principal=principal)
    except ScopeControlError as exc:
        raise _http_error(exc) from exc


@router.post(
    "/projects/{project_id}/scope-change-requests",
    response_model=ScopeChangeView,
    status_code=status.HTTP_201_CREATED,
)
async def create_scope_change_request(
    project_id: uuid.UUID,
    body: ScopeChangeCreate,
    principal: Annotated[
        SessionPrincipal,
        Depends(
            require_roles(
                Role.CLIENT_OWNER,
                Role.CLIENT_MEMBER,
                Role.STUDENT,
                Role.TECHNICAL_LEAD,
            )
        ),
    ],
    session: DbSession,
) -> ScopeChangeRequest:
    try:
        return await request_scope_change(
            session,
            project_id=project_id,
            principal=principal,
            request=body,
        )
    except ScopeControlError as exc:
        raise _http_error(exc) from exc


@router.get(
    "/projects/{project_id}/change-orders",
    response_model=list[ChangeOrderView],
)
async def get_change_orders(
    project_id: uuid.UUID, principal: Principal, session: DbSession
) -> list[ChangeOrder]:
    try:
        return await list_change_orders(session, project_id=project_id, principal=principal)
    except ScopeControlError as exc:
        raise _http_error(exc) from exc


@router.post(
    "/ops/projects/{project_id}/change-orders",
    response_model=ChangeOrderView,
    status_code=status.HTTP_201_CREATED,
)
async def draft_change_order(
    project_id: uuid.UUID,
    body: ChangeOrderCreate,
    principal: Annotated[SessionPrincipal, Depends(require_roles(Role.COORDINATOR))],
    session: DbSession,
) -> ChangeOrder:
    try:
        return await create_change_order(
            session,
            project_id=project_id,
            principal=principal,
            request=body,
        )
    except ScopeControlError as exc:
        raise _http_error(exc) from exc


@router.post(
    "/projects/{project_id}/change-orders/{change_order_id}/client-decision",
    response_model=ChangeOrderView,
)
async def client_change_order_decision(
    project_id: uuid.UUID,
    change_order_id: uuid.UUID,
    body: ChangeOrderDecision,
    principal: Annotated[SessionPrincipal, Depends(require_roles(Role.CLIENT_OWNER))],
    session: DbSession,
) -> ChangeOrder:
    try:
        return await decide_change_order(
            session,
            project_id=project_id,
            change_order_id=change_order_id,
            principal=principal,
            decision=body.decision,
            reason=body.reason,
        )
    except ScopeControlError as exc:
        raise _http_error(exc) from exc
