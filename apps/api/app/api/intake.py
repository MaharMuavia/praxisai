import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.auth.dependencies import DbSession, IdempotencyKey, correlation_id, require_roles
from app.auth.service import SessionPrincipal
from app.domain.enums import Role
from app.domain.models import PublicIntakeSubmission
from app.domain.schemas import (
    PublicIntakeReceipt,
    PublicIntakeSubmissionCreate,
    PublicIntakeSubmissionUpdate,
    PublicIntakeSubmissionView,
)
from app.intake.service import create_submission, list_submissions, update_submission
from app.rate_limits.service import RateLimitExceeded, consume_rate_limit

router = APIRouter(tags=["public intake"])
OperationsPrincipal = Annotated[
    SessionPrincipal,
    Depends(require_roles(Role.COORDINATOR, Role.PLATFORM_ADMIN)),
]


async def _limit_public_submission(session: DbSession, request: Request, email: str) -> None:
    client_host = request.client.host if request.client else "unknown"
    try:
        await consume_rate_limit(
            session, raw_key=f"public-intake:ip:{client_host}", limit=10, window_seconds=3600
        )
        await consume_rate_limit(
            session, raw_key=f"public-intake:email:{email.lower()}", limit=3, window_seconds=86400
        )
    except RateLimitExceeded as exc:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, str(exc)) from exc


@router.post(
    "/public/{kind}", response_model=PublicIntakeReceipt, status_code=status.HTTP_201_CREATED
)
async def submit_public_intake(
    kind: str,
    body: PublicIntakeSubmissionCreate,
    request: Request,
    session: DbSession,
    idempotency_key: IdempotencyKey,
) -> PublicIntakeReceipt:
    if kind != body.kind:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Intake kind does not match the route")
    if body.honeypot:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Unable to accept this submission")
    await _limit_public_submission(session, request, body.email)
    submission = await create_submission(
        session,
        body=body,
        idempotency_key=idempotency_key,
        correlation_id=correlation_id(request),
    )
    return PublicIntakeReceipt(
        id=submission.id,
        kind=submission.kind,
        status=submission.status,
        received_at=submission.created_at,
        correlation_id=submission.correlation_id,
    )


@router.get("/ops/intake", response_model=list[PublicIntakeSubmissionView])
async def intake_queue(
    principal: OperationsPrincipal,
    session: DbSession,
    submission_status: Annotated[str | None, Query(alias="status", max_length=32)] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> list[PublicIntakeSubmission]:
    return await list_submissions(session, status=submission_status, limit=limit)


@router.patch("/ops/intake/{submission_id}", response_model=PublicIntakeSubmissionView)
async def review_intake(
    submission_id: uuid.UUID,
    body: PublicIntakeSubmissionUpdate,
    principal: OperationsPrincipal,
    session: DbSession,
    request: Request,
) -> PublicIntakeSubmission:
    try:
        return await update_submission(
            session,
            submission_id=submission_id,
            body=body,
            principal=principal,
            correlation_id=correlation_id(request),
        )
    except LookupError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
