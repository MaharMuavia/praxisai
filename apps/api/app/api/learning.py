import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.dependencies import DbSession, correlation_id, require_roles
from app.auth.service import SessionPrincipal
from app.domain.enums import Role
from app.domain.schemas import LearningModuleCompleteRequest, LearningPathView
from app.learning.service import (
    LearningError,
    LearningNotFound,
    complete_module,
    enroll_in_path,
    list_learning_paths,
)

router = APIRouter(prefix="/learning", tags=["learning"])
StudentPrincipal = Annotated[SessionPrincipal, Depends(require_roles(Role.STUDENT))]


@router.get("/paths", response_model=list[LearningPathView])
async def paths(principal: StudentPrincipal, session: DbSession) -> list[LearningPathView]:
    return await list_learning_paths(session, principal=principal)


@router.post("/paths/{path_id}/enroll", response_model=LearningPathView)
async def enroll(
    path_id: uuid.UUID,
    principal: StudentPrincipal,
    session: DbSession,
    request_correlation_id: Annotated[uuid.UUID, Depends(correlation_id)],
) -> LearningPathView:
    try:
        return await enroll_in_path(
            session,
            path_id=path_id,
            principal=principal,
            correlation_id=request_correlation_id,
        )
    except LearningNotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except LearningError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc


@router.post("/modules/{module_id}/complete", response_model=LearningPathView)
async def complete(
    module_id: uuid.UUID,
    body: LearningModuleCompleteRequest,
    principal: StudentPrincipal,
    session: DbSession,
    request_correlation_id: Annotated[uuid.UUID, Depends(correlation_id)],
) -> LearningPathView:
    try:
        return await complete_module(
            session,
            module_id=module_id,
            body=body,
            principal=principal,
            correlation_id=request_correlation_id,
        )
    except LearningNotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except LearningError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
