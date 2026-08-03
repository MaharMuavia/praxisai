import ipaddress
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.auth.dependencies import DbSession, IdempotencyKey, correlation_id, require_roles
from app.auth.service import SessionPrincipal
from app.config import Settings, get_settings
from app.domain.enums import Role
from app.domain.models import PublicIntakeSubmission
from app.domain.schemas import (
    PublicIntakeReceipt,
    PublicIntakeSubmissionCreate,
    PublicIntakeSubmissionUpdate,
    PublicIntakeSubmissionView,
)
from app.intake.service import (
    IdempotencyConflict,
    IntakeVersionConflict,
    InvalidIntakeTransition,
    anonymize_submission,
    create_submission,
    ensure_idempotency_matches,
    find_submission,
    get_submission,
    list_submissions,
    submission_payload_hash,
    update_submission,
)
from app.rate_limits.service import RateLimitExceeded, consume_rate_limit

router = APIRouter(tags=["public intake"])
OperationsPrincipal = Annotated[
    SessionPrincipal,
    Depends(require_roles(Role.COORDINATOR, Role.PLATFORM_ADMIN)),
]


def _client_ip(request: Request, settings: Settings) -> str:
    peer = request.client.host if request.client else "unknown"
    try:
        trusted = {ipaddress.ip_address(value) for value in settings.trusted_proxy_ips}
        peer_address = ipaddress.ip_address(peer)
    except ValueError:
        return peer
    if peer_address not in trusted:
        return peer
    forwarded = request.headers.get("X-Forwarded-For", "")
    first = forwarded.split(",", maxsplit=1)[0].strip()
    try:
        ipaddress.ip_address(first)
    except ValueError:
        return peer
    return first


async def _limit_public_submission(
    session: DbSession, request: Request, email: str, settings: Settings
) -> None:
    client_host = _client_ip(request, settings)
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
    settings: Annotated[Settings, Depends(get_settings)],
) -> PublicIntakeReceipt:
    if kind != body.kind:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Intake kind does not match the route")
    if body.honeypot:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Unable to accept this submission")
    existing = await find_submission(session, idempotency_key=idempotency_key)
    if existing is not None:
        try:
            ensure_idempotency_matches(existing, payload_hash=submission_payload_hash(body))
        except IdempotencyConflict as exc:
            raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
        submission = existing
    else:
        await _limit_public_submission(session, request, body.email, settings)
        try:
            submission = await create_submission(
                session,
                body=body,
                idempotency_key=idempotency_key,
                correlation_id=correlation_id(request),
            )
        except IdempotencyConflict as exc:
            raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
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
    except IntakeVersionConflict as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
    except (InvalidIntakeTransition, ValueError) as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc


@router.get("/ops/intake/{submission_id}", response_model=PublicIntakeSubmissionView)
async def intake_detail(
    submission_id: uuid.UUID,
    principal: OperationsPrincipal,
    session: DbSession,
) -> PublicIntakeSubmission:
    try:
        return await get_submission(session, submission_id=submission_id)
    except LookupError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc


@router.post("/ops/intake/{submission_id}/anonymize", response_model=PublicIntakeSubmissionView)
async def anonymize_intake(
    submission_id: uuid.UUID,
    principal: OperationsPrincipal,
    session: DbSession,
    request: Request,
) -> PublicIntakeSubmission:
    try:
        return await anonymize_submission(
            session,
            submission_id=submission_id,
            principal=principal,
            correlation_id=correlation_id(request),
        )
    except LookupError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
