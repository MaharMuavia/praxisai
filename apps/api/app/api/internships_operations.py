import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.auth.dependencies import DbSession, IdempotencyKey, require_capability
from app.auth.service import SessionPrincipal
from app.domain.models import InternshipReview
from app.internships.reviews.service import ReviewAssignmentError, assign_reviewer
from app.internships.schemas import (
    ApplicationDecisionRequest,
    ApplicationView,
    CompletionDecisionRequest,
    IssueCertificateRequest,
    OperationsApplicationView,
    ReviewAssignRequest,
    ReviewFinalizeRequest,
    ReviewQueueItem,
)
from app.internships.service import (
    Conflict,
    Forbidden,
    InternshipError,
    NotFound,
    decide_application,
    decide_completion,
    finalize_review,
    issue_certificate,
    list_operations_applications,
    review_queue,
)

router = APIRouter(prefix="/ops/internships", tags=["internships operations"])
ApplicationsPrincipal = Annotated[
    SessionPrincipal, Depends(require_capability("internships:applications:view"))
]
DecisionPrincipal = Annotated[
    SessionPrincipal, Depends(require_capability("internships:applications:decide"))
]
ReviewAssignPrincipal = Annotated[
    SessionPrincipal, Depends(require_capability("internships:reviews:assign"))
]
ReviewViewPrincipal = Annotated[
    SessionPrincipal, Depends(require_capability("internships:reviews:view_assigned"))
]
ReviewFinalizePrincipal = Annotated[
    SessionPrincipal, Depends(require_capability("internships:reviews:finalize"))
]
CertificatePrincipal = Annotated[
    SessionPrincipal, Depends(require_capability("internships:certificates:issue"))
]
CompletionPrincipal = Annotated[
    SessionPrincipal, Depends(require_capability("internships:completion:decide"))
]


def _raise(error: InternshipError) -> None:
    code = (
        status.HTTP_404_NOT_FOUND
        if isinstance(error, NotFound)
        else status.HTTP_409_CONFLICT
        if isinstance(error, Conflict)
        else status.HTTP_403_FORBIDDEN
        if isinstance(error, Forbidden)
        else status.HTTP_400_BAD_REQUEST
    )
    raise HTTPException(code, detail={"code": error.code, "message": str(error)}) from error


@router.get("/applications", response_model=list[OperationsApplicationView])
async def applications(
    principal: ApplicationsPrincipal,
    session: DbSession,
    limit: int = 50,
    offset: int = 0,
) -> list[OperationsApplicationView]:
    del principal
    if limit < 1 or limit > 100 or offset < 0:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid pagination")
    return await list_operations_applications(session, limit=limit, offset=offset)


@router.post("/applications/{application_id}/decision", response_model=ApplicationView)
async def application_decision(
    application_id: uuid.UUID,
    body: ApplicationDecisionRequest,
    principal: DecisionPrincipal,
    session: DbSession,
    request: Request,
) -> ApplicationView:
    try:
        return await decide_application(
            session,
            application_id=application_id,
            principal=principal,
            body=body,
            correlation_id=request.state.correlation_id,
        )
    except InternshipError as exc:
        _raise(exc)
    raise AssertionError("unreachable")


@router.get("/reviews", response_model=list[ReviewQueueItem])
async def reviews(
    principal: ReviewViewPrincipal,
    session: DbSession,
    limit: int = 50,
    offset: int = 0,
) -> list[ReviewQueueItem]:
    return await review_queue(session, principal=principal, limit=limit, offset=offset)


@router.post("/reviews/{review_id}/assign", response_model=ReviewQueueItem)
async def assign_review(
    review_id: uuid.UUID,
    body: ReviewAssignRequest,
    principal: ReviewAssignPrincipal,
    session: DbSession,
    request: Request,
) -> ReviewQueueItem:
    review = await session.get(InternshipReview, review_id)
    if review is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Review not found")
    try:
        await assign_reviewer(
            session,
            review=review,
            reviewer_id=body.reviewer_id,
            principal=principal,
            correlation_id=request.state.correlation_id,
        )
    except ReviewAssignmentError as exc:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail={"code": "reviewer_not_eligible", "message": str(exc)},
        ) from exc
    await session.commit()
    rows = await review_queue(session, principal=principal, limit=100, offset=0)
    selected = next((row for row in rows if row.review_id == review_id), None)
    if selected is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Review not found")
    return selected


@router.post("/reviews/{review_id}/finalize", response_model=ReviewQueueItem)
async def finalize_review_route(
    review_id: uuid.UUID,
    body: ReviewFinalizeRequest,
    principal: ReviewFinalizePrincipal,
    session: DbSession,
    request: Request,
    idempotency_key: IdempotencyKey,
) -> ReviewQueueItem:
    try:
        return await finalize_review(
            session,
            review_id=review_id,
            principal=principal,
            body=body,
            correlation_id=request.state.correlation_id,
            idempotency_key=idempotency_key,
        )
    except InternshipError as exc:
        _raise(exc)
    raise AssertionError("unreachable")


@router.post("/enrollments/{enrollment_id}/issue-certificate", status_code=201)
async def issue_certificate_route(
    enrollment_id: uuid.UUID,
    body: IssueCertificateRequest,
    principal: CertificatePrincipal,
    session: DbSession,
    idempotency_key: IdempotencyKey,
    request: Request,
) -> dict[str, object]:
    try:
        certificate = await issue_certificate(
            session,
            enrollment_id=enrollment_id,
            principal=principal,
            confirm=body.confirm,
            idempotency_key=idempotency_key,
            correlation_id=request.state.correlation_id,
        )
    except InternshipError as exc:
        _raise(exc)
    return {
        "id": certificate.id,
        "state": certificate.state,
        "public_slug": certificate.public_slug,
    }


@router.post("/enrollments/{enrollment_id}/completion-decision")
async def completion_decision_route(
    enrollment_id: uuid.UUID,
    body: CompletionDecisionRequest,
    principal: CompletionPrincipal,
    session: DbSession,
    request: Request,
    idempotency_key: IdempotencyKey,
) -> object:
    try:
        return await decide_completion(
            session,
            enrollment_id=enrollment_id,
            principal=principal,
            decision=body.decision,
            reason=body.reason,
            expected_version=body.expected_version,
            idempotency_key=idempotency_key,
            correlation_id=request.state.correlation_id,
        )
    except InternshipError as exc:
        _raise(exc)
    raise AssertionError("unreachable")
