import uuid
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Request, status

from app.auth.dependencies import DbSession, Principal
from app.domain.schemas import (
    NotificationPreferenceUpdate,
    NotificationPreferenceView,
    NotificationView,
)
from app.notifications.service import (
    NotificationConflict,
    NotificationNotFound,
    list_preferences,
    list_user_notifications,
    mark_notification_read,
    update_preference,
)

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=list[NotificationView])
async def list_notifications(
    principal: Principal,
    session: DbSession,
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
) -> list[NotificationView]:
    rows = await list_user_notifications(session, user_id=principal.user_id, limit=limit)
    return [NotificationView.model_validate(row) for row in rows]


@router.post("/{notification_id}/read", status_code=status.HTTP_204_NO_CONTENT)
async def mark_read(notification_id: uuid.UUID, principal: Principal, session: DbSession) -> None:
    try:
        await mark_notification_read(
            session, user_id=principal.user_id, notification_id=notification_id
        )
    except NotificationNotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc


@router.get("/preferences", response_model=list[NotificationPreferenceView])
async def preferences(principal: Principal, session: DbSession) -> list[NotificationPreferenceView]:
    return await list_preferences(session, user_id=principal.user_id)


@router.put("/preferences", response_model=NotificationPreferenceView)
async def set_preference(
    body: NotificationPreferenceUpdate,
    principal: Principal,
    session: DbSession,
    request: Request,
) -> NotificationPreferenceView:
    try:
        return await update_preference(
            session,
            principal=principal,
            update=body,
            correlation_id=request.state.correlation_id,
        )
    except NotificationConflict as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
    except NotificationNotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
