import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.auth.dependencies import DbSession, IdempotencyKey, correlation_id, require_roles
from app.auth.service import SessionPrincipal
from app.domain.enums import Role
from app.domain.models import PublicIntakeSubmission, User
from app.domain.schemas import (
    PublicIntakeAuditView,
    PublicIntakeOwnerView,
    PublicIntakeQueueResponse,
    PublicIntakeReason,
    PublicIntakeReceipt,
    PublicIntakeSubmissionCreate,
    PublicIntakeSubmissionUpdate,
    PublicIntakeSubmissionView,
)
from app.intake.service import (
    IdempotencyConflict,
    IntakeVersionConflict,
    InvalidIntakeTransition,
    allowed_transitions,
    anonymize_submission,
    create_submission,
    delete_submission,
    get_submission,
    list_audit_events,
    list_owners,
    list_submission_summaries,
    mark_idempotency_failed,
    request_withdrawal,
    reserve_idempotency,
    submission_payload_hash,
    update_submission,
)
from app.rate_limits.service import (
    RateLimitExceeded,
    consume_rate_limit,
    opaque_rate_limit_key,
)

router = APIRouter(tags=["public intake"])
OperationsPrincipal = Annotated[
    SessionPrincipal,
    Depends(require_roles(Role.COORDINATOR, Role.PLATFORM_ADMIN)),
]

PUBLIC_INTAKE_EMAIL_LIMIT = 3
PUBLIC_INTAKE_EMAIL_WINDOW_SECONDS = 86_400
PUBLIC_INTAKE_GLOBAL_LIMIT = 1_000
PUBLIC_INTAKE_GLOBAL_WINDOW_SECONDS = 3_600


async def _limit_public_submission(session: DbSession, email: str) -> None:
    try:
        await consume_rate_limit(
            session,
            raw_key=opaque_rate_limit_key(
                namespace="public-intake:email",
                identifier=email.strip().casefold(),
            ),
            limit=PUBLIC_INTAKE_EMAIL_LIMIT,
            window_seconds=PUBLIC_INTAKE_EMAIL_WINDOW_SECONDS,
            commit=False,
        )
        await consume_rate_limit(
            session,
            raw_key="public-intake:global",
            limit=PUBLIC_INTAKE_GLOBAL_LIMIT,
            window_seconds=PUBLIC_INTAKE_GLOBAL_WINDOW_SECONDS,
            commit=False,
        )
        await session.commit()
    except RateLimitExceeded as exc:
        await session.rollback()
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, str(exc)) from exc


def _view(submission: PublicIntakeSubmission) -> dict[str, object]:
    return {
        "id": submission.id,
        "kind": submission.kind,
        "status": submission.status,
        "contact_email": submission.contact_email,
        "source": submission.source,
        "campaign": submission.campaign,
        "payload": submission.payload,
        "owner_id": submission.owner_id,
        "qualification_notes": submission.qualification_notes,
        "rejection_reason": submission.rejection_reason,
        "reviewed_at": submission.reviewed_at,
        "created_at": submission.created_at,
        "correlation_id": submission.correlation_id,
        "version": submission.version,
        "conversion_evidence": submission.conversion_evidence,
        "retention_expires_at": submission.retention_expires_at,
        "anonymized_at": submission.anonymized_at,
        "deleted_at": submission.deleted_at,
        "withdrawal_requested_at": submission.withdrawal_requested_at,
        "allowed_transitions": allowed_transitions(submission),
    }


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
    try:
        reserved_submission = await reserve_idempotency(
            session,
            idempotency_key=idempotency_key,
            payload_hash=submission_payload_hash(body),
            kind=body.kind,
            correlation_id=correlation_id(request),
        )
        if reserved_submission is not None:
            submission = reserved_submission
        else:
            await _limit_public_submission(session, body.email)
            submission = await create_submission(
                session,
                body=body,
                idempotency_key=idempotency_key,
                correlation_id=correlation_id(request),
            )
    except IdempotencyConflict as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
    except Exception:
        await mark_idempotency_failed(session, idempotency_key=idempotency_key)
        raise
    return PublicIntakeReceipt(
        id=submission.id,
        kind=submission.kind,
        status=submission.status,
        received_at=submission.created_at,
        correlation_id=submission.correlation_id,
    )


@router.get("/ops/intake", response_model=PublicIntakeQueueResponse)
async def intake_queue(
    principal: OperationsPrincipal,
    session: DbSession,
    submission_status: Annotated[str | None, Query(alias="status", max_length=32)] = None,
    kind: Annotated[str | None, Query(max_length=32)] = None,
    owner_id: uuid.UUID | None = None,
    source: Annotated[str | None, Query(max_length=120)] = None,
    search: Annotated[str | None, Query(max_length=160)] = None,
    action_required: bool | None = None,
    cursor: Annotated[str | None, Query(max_length=500)] = None,
    page_size: Annotated[int, Query(ge=1, le=100)] = 50,
) -> PublicIntakeQueueResponse:
    try:
        rows, next_cursor = await list_submission_summaries(
            session,
            status=submission_status,
            kind=kind,
            owner_id=owner_id,
            source=source,
            search=search,
            action_required=action_required,
            cursor=cursor,
            page_size=page_size,
        )
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    return PublicIntakeQueueResponse(
        items=[
            {
                "id": row.id,
                "kind": row.kind,
                "status": row.status,
                "display_name": str(row.payload.get("full_name", "Unnamed contact")),
                "source": row.source,
                "campaign": row.campaign,
                "owner_id": row.owner_id,
                "created_at": row.created_at,
                "retention_expires_at": row.retention_expires_at,
                "anonymized_at": row.anonymized_at,
                "withdrawal_requested_at": row.withdrawal_requested_at,
                "action_required": row.status in {"NEW", "IN_REVIEW"},
            }
            for row in rows
        ],
        next_cursor=next_cursor,
    )


@router.get("/ops/intake/owners", response_model=list[PublicIntakeOwnerView])
async def intake_owners(principal: OperationsPrincipal, session: DbSession) -> list[User]:
    return await list_owners(session)


@router.patch("/ops/intake/{submission_id}", response_model=PublicIntakeSubmissionView)
async def review_intake(
    submission_id: uuid.UUID,
    body: PublicIntakeSubmissionUpdate,
    principal: OperationsPrincipal,
    session: DbSession,
    request: Request,
) -> dict[str, object]:
    try:
        submission = await update_submission(
            session,
            submission_id=submission_id,
            body=body,
            principal=principal,
            correlation_id=correlation_id(request),
        )
        return _view(submission)
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
) -> dict[str, object]:
    try:
        return _view(await get_submission(session, submission_id=submission_id))
    except LookupError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc


@router.get("/ops/intake/{submission_id}/audit", response_model=list[PublicIntakeAuditView])
async def intake_audit(
    submission_id: uuid.UUID,
    principal: OperationsPrincipal,
    session: DbSession,
) -> list[dict[str, object]]:
    try:
        await get_submission(session, submission_id=submission_id)
    except LookupError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    return [
        {
            "id": row.id,
            "action": row.action,
            "resource_id": row.resource_id,
            "correlation_id": row.correlation_id,
            "payload": row.payload,
            "created_at": row.created_at,
        }
        for row in await list_audit_events(session, submission_id=submission_id)
    ]


@router.post("/ops/intake/{submission_id}/anonymize", response_model=PublicIntakeSubmissionView)
async def anonymize_intake(
    submission_id: uuid.UUID,
    principal: OperationsPrincipal,
    session: DbSession,
    request: Request,
) -> dict[str, object]:
    try:
        return _view(
            await anonymize_submission(
                session,
                submission_id=submission_id,
                principal=principal,
                correlation_id=correlation_id(request),
            )
        )
    except LookupError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc


@router.post("/ops/intake/{submission_id}/withdraw", response_model=PublicIntakeSubmissionView)
async def withdraw_intake(
    submission_id: uuid.UUID,
    body: PublicIntakeReason,
    principal: OperationsPrincipal,
    session: DbSession,
    request: Request,
) -> dict[str, object]:
    try:
        return _view(
            await request_withdrawal(
                session,
                submission_id=submission_id,
                principal=principal,
                reason=body.reason,
                correlation_id=correlation_id(request),
            )
        )
    except LookupError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc


@router.post("/ops/intake/{submission_id}/delete", status_code=status.HTTP_204_NO_CONTENT)
async def delete_intake(
    submission_id: uuid.UUID,
    body: PublicIntakeReason,
    principal: OperationsPrincipal,
    session: DbSession,
    request: Request,
) -> None:
    try:
        await delete_submission(
            session,
            submission_id=submission_id,
            principal=principal,
            reason=body.reason,
            correlation_id=correlation_id(request),
        )
    except LookupError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
