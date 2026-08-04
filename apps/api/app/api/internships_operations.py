import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.auth.dependencies import DbSession, IdempotencyKey, require_roles
from app.auth.service import SessionPrincipal
from app.domain.enums import Role
from app.domain.models import InternshipReview, InternshipStudentAssignment
from app.internships.schemas import (
    ApplicationDecisionRequest,
    ApplicationView,
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
    finalize_review,
    issue_certificate,
    list_operations_applications,
    review_queue,
)

router = APIRouter(prefix="/ops/internships", tags=["internships operations"])
OperationsPrincipal = Annotated[
    SessionPrincipal,
    Depends(
        require_roles(Role.COORDINATOR, Role.PLATFORM_ADMIN, Role.REVIEWER, Role.TECHNICAL_LEAD)
    ),
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
    principal: OperationsPrincipal,
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
    principal: OperationsPrincipal,
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
    principal: OperationsPrincipal,
    session: DbSession,
    limit: int = 50,
    offset: int = 0,
) -> list[ReviewQueueItem]:
    del principal
    return await review_queue(session, limit=limit, offset=offset)


@router.post("/reviews/{review_id}/assign", response_model=ReviewQueueItem)
async def assign_review(
    review_id: uuid.UUID,
    body: ReviewAssignRequest,
    principal: OperationsPrincipal,
    session: DbSession,
    request: Request,
) -> ReviewQueueItem:
    review = await session.get(InternshipReview, review_id)
    if review is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Review not found")
    reviewer = await session.get(InternshipStudentAssignment, review.student_assignment_id)
    if reviewer is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Assignment not found")
    review.reviewer_id = body.reviewer_id
    review.status = "ASSIGNED"
    await session.commit()
    rows = await review_queue(session, limit=100, offset=0)
    selected = next((row for row in rows if row.review_id == review_id), None)
    if selected is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Review not found")
    return selected


@router.post("/reviews/{review_id}/finalize", response_model=ReviewQueueItem)
async def finalize_review_route(
    review_id: uuid.UUID,
    body: ReviewFinalizeRequest,
    principal: OperationsPrincipal,
    session: DbSession,
    request: Request,
) -> ReviewQueueItem:
    try:
        return await finalize_review(
            session,
            review_id=review_id,
            principal=principal,
            body=body,
            correlation_id=request.state.correlation_id,
        )
    except InternshipError as exc:
        _raise(exc)
    raise AssertionError("unreachable")


@router.post("/enrollments/{enrollment_id}/issue-certificate", status_code=201)
async def issue_certificate_route(
    enrollment_id: uuid.UUID,
    body: IssueCertificateRequest,
    principal: OperationsPrincipal,
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
