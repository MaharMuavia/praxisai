import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.auth.dependencies import DbSession, IdempotencyKey, require_roles
from app.auth.service import SessionPrincipal
from app.config import Settings, get_settings
from app.domain.enums import Role
from app.domain.schemas import (
    SubmissionAIReviewRequest,
    SubmissionAIReviewResponse,
)
from app.internships.schemas import (
    ApplicationSubmitRequest,
    ApplicationSummary,
    ApplicationUpdate,
    ApplicationView,
    AssignmentView,
    CertificateEligibilityView,
    CurriculumView,
    DashboardView,
    FeedbackView,
    FinalizeSubmissionRequest,
    ResubmissionRequest,
    StartApplicationRequest,
    SubmissionDraftRequest,
    SubmissionUpdateRequest,
    SubmissionView,
    UnitCompletionRequest,
)
from app.internships.service import (
    Conflict,
    Forbidden,
    InternshipError,
    NotFound,
    certificate_eligibility,
    complete_unit,
    create_submission_draft,
    curriculum,
    dashboard,
    feedback,
    finalize_submission,
    get_application,
    get_assignment,
    get_submission,
    list_applications,
    list_assignments,
    resubmit,
    review_submission_with_ai,
    save_submission,
    start_application,
    start_assignment,
    submit_application,
    update_application,
)

router = APIRouter(prefix="/internships/me", tags=["internships student"])
StudentPrincipal = Annotated[SessionPrincipal, Depends(require_roles(Role.STUDENT))]


def _raise(error: InternshipError) -> None:
    if isinstance(error, NotFound):
        code = status.HTTP_404_NOT_FOUND
    elif isinstance(error, Forbidden):
        code = status.HTTP_403_FORBIDDEN
    elif isinstance(error, Conflict):
        code = status.HTTP_409_CONFLICT
    else:
        code = status.HTTP_400_BAD_REQUEST
    raise HTTPException(code, detail={"code": error.code, "message": str(error)}) from error


async def _single_application_id(principal: StudentPrincipal, session: DbSession) -> uuid.UUID:
    rows = await list_applications(session, principal)
    if not rows:
        _raise(NotFound("Internship application not found"))
    if len(rows) != 1:
        _raise(Conflict("Select an application explicitly"))
    return rows[0].id


@router.get("/applications", response_model=list[ApplicationSummary])
async def applications(principal: StudentPrincipal, session: DbSession) -> list[ApplicationSummary]:
    return await list_applications(session, principal)


@router.post("/applications", response_model=ApplicationView, status_code=201)
async def create_application(
    body: StartApplicationRequest,
    principal: StudentPrincipal,
    session: DbSession,
    request: Request,
) -> ApplicationView:
    try:
        return await start_application(
            session, principal=principal, body=body, correlation_id=request.state.correlation_id
        )
    except InternshipError as exc:
        _raise(exc)
    raise AssertionError("unreachable")


@router.get("/applications/{application_id}", response_model=ApplicationView)
async def application_by_id(
    application_id: uuid.UUID, principal: StudentPrincipal, session: DbSession
) -> ApplicationView:
    try:
        return await get_application(session, principal=principal, application_id=application_id)
    except InternshipError as exc:
        _raise(exc)
    raise AssertionError("unreachable")


@router.put("/applications/{application_id}", response_model=ApplicationView)
async def update_application_by_id(
    application_id: uuid.UUID,
    body: ApplicationUpdate,
    principal: StudentPrincipal,
    session: DbSession,
    request: Request,
) -> ApplicationView:
    try:
        return await update_application(
            session,
            principal=principal,
            application_id=application_id,
            body=body,
            correlation_id=request.state.correlation_id,
        )
    except InternshipError as exc:
        _raise(exc)
    raise AssertionError("unreachable")


@router.post("/applications/{application_id}/submit", response_model=ApplicationView)
async def submit_application_by_id(
    application_id: uuid.UUID,
    body: ApplicationSubmitRequest,
    principal: StudentPrincipal,
    session: DbSession,
    idempotency_key: IdempotencyKey,
    request: Request,
) -> ApplicationView:
    try:
        return await submit_application(
            session,
            principal=principal,
            application_id=application_id,
            expected_version=body.expected_version,
            consent_version=body.consent_version,
            idempotency_key=idempotency_key,
            correlation_id=request.state.correlation_id,
        )
    except InternshipError as exc:
        _raise(exc)
    raise AssertionError("unreachable")


@router.get("/application", response_model=ApplicationView)
async def legacy_application(principal: StudentPrincipal, session: DbSession) -> ApplicationView:
    try:
        application_id = await _single_application_id(principal, session)
        return await get_application(session, principal=principal, application_id=application_id)
    except InternshipError as exc:
        _raise(exc)
    raise AssertionError("unreachable")


@router.post("/application/start", response_model=ApplicationView, status_code=201)
async def start_application_route(
    body: StartApplicationRequest,
    principal: StudentPrincipal,
    session: DbSession,
    request: Request,
) -> ApplicationView:
    try:
        return await start_application(
            session, principal=principal, body=body, correlation_id=request.state.correlation_id
        )
    except InternshipError as exc:
        _raise(exc)
    raise AssertionError("unreachable")


@router.put("/application", response_model=ApplicationView)
async def update_application_route(
    body: ApplicationUpdate,
    principal: StudentPrincipal,
    session: DbSession,
    request: Request,
) -> ApplicationView:
    try:
        return await update_application(
            session,
            principal=principal,
            application_id=await _single_application_id(principal, session),
            body=body,
            correlation_id=request.state.correlation_id,
        )
    except InternshipError as exc:
        _raise(exc)
    raise AssertionError("unreachable")


@router.post("/application/submit", response_model=ApplicationView)
async def submit_application_route(
    body: ApplicationSubmitRequest,
    principal: StudentPrincipal,
    session: DbSession,
    idempotency_key: IdempotencyKey,
    request: Request,
) -> ApplicationView:
    try:
        return await submit_application(
            session,
            principal=principal,
            application_id=await _single_application_id(principal, session),
            expected_version=body.expected_version,
            consent_version=body.consent_version,
            idempotency_key=idempotency_key,
            correlation_id=request.state.correlation_id,
        )
    except InternshipError as exc:
        _raise(exc)
    raise AssertionError("unreachable")


@router.get("/dashboard", response_model=DashboardView)
async def dashboard_route(
    principal: StudentPrincipal,
    session: DbSession,
    enrollment_id: uuid.UUID | None = None,
) -> DashboardView:
    return await dashboard(session, principal, enrollment_id)


@router.get("/curriculum", response_model=CurriculumView)
async def curriculum_route(
    principal: StudentPrincipal,
    session: DbSession,
    enrollment_id: uuid.UUID | None = None,
) -> CurriculumView:
    try:
        return await curriculum(session, principal, enrollment_id)
    except InternshipError as exc:
        _raise(exc)
    raise AssertionError("unreachable")


@router.post("/curriculum/units/{unit_id}/complete", response_model=CurriculumView)
async def complete_unit_route(
    unit_id: uuid.UUID,
    body: UnitCompletionRequest,
    principal: StudentPrincipal,
    session: DbSession,
    request: Request,
    enrollment_id: uuid.UUID | None = None,
) -> CurriculumView:
    try:
        return await complete_unit(
            session,
            principal=principal,
            unit_id=unit_id,
            enrollment_id=enrollment_id,
            evidence={
                "summary": body.evidence_summary,
                "url": str(body.evidence_url) if body.evidence_url else None,
            },
            correlation_id=request.state.correlation_id,
        )
    except InternshipError as exc:
        _raise(exc)
    raise AssertionError("unreachable")


@router.get("/assignments", response_model=list[AssignmentView])
async def assignments(
    principal: StudentPrincipal,
    session: DbSession,
    enrollment_id: uuid.UUID | None = None,
) -> list[AssignmentView]:
    try:
        return await list_assignments(session, principal, enrollment_id)
    except InternshipError as exc:
        _raise(exc)
    raise AssertionError("unreachable")


@router.get("/assignments/{assignment_id}", response_model=AssignmentView)
async def assignment(
    assignment_id: uuid.UUID,
    principal: StudentPrincipal,
    session: DbSession,
    enrollment_id: uuid.UUID | None = None,
) -> AssignmentView:
    try:
        row = await get_assignment(
            session,
            principal=principal,
            assignment_id=assignment_id,
            enrollment_id=enrollment_id,
        )
        from app.internships.service import _assignment_view

        return await _assignment_view(session, row)
    except InternshipError as exc:
        _raise(exc)
    raise AssertionError("unreachable")


@router.post("/assignments/{assignment_id}/start", response_model=AssignmentView)
async def start_assignment_route(
    assignment_id: uuid.UUID,
    principal: StudentPrincipal,
    session: DbSession,
    request: Request,
    enrollment_id: uuid.UUID | None = None,
) -> AssignmentView:
    try:
        return await start_assignment(
            session,
            principal=principal,
            assignment_id=assignment_id,
            enrollment_id=enrollment_id,
            correlation_id=request.state.correlation_id,
        )
    except InternshipError as exc:
        _raise(exc)
    raise AssertionError("unreachable")


@router.post("/assignments/{assignment_id}/submission-drafts", response_model=SubmissionView)
async def submission_draft(
    assignment_id: uuid.UUID,
    body: SubmissionDraftRequest,
    principal: StudentPrincipal,
    session: DbSession,
    request: Request,
    enrollment_id: uuid.UUID | None = None,
) -> SubmissionView:
    try:
        return await create_submission_draft(
            session,
            principal=principal,
            assignment_id=assignment_id,
            enrollment_id=enrollment_id,
            body=body,
            correlation_id=request.state.correlation_id,
        )
    except InternshipError as exc:
        _raise(exc)
    raise AssertionError("unreachable")


@router.put("/submissions/{submission_id}", response_model=SubmissionView)
async def update_submission(
    submission_id: uuid.UUID,
    body: SubmissionUpdateRequest,
    principal: StudentPrincipal,
    session: DbSession,
) -> SubmissionView:
    try:
        return await save_submission(
            session, principal=principal, submission_id=submission_id, body=body
        )
    except InternshipError as exc:
        _raise(exc)
    raise AssertionError("unreachable")


@router.get("/submissions/{submission_id}", response_model=SubmissionView)
async def submission(
    submission_id: uuid.UUID,
    principal: StudentPrincipal,
    session: DbSession,
) -> SubmissionView:
    try:
        return await get_submission(session, principal=principal, submission_id=submission_id)
    except InternshipError as exc:
        _raise(exc)
    raise AssertionError("unreachable")


@router.post("/submissions/{submission_id}/finalize", response_model=SubmissionView)
async def finalize_submission_route(
    submission_id: uuid.UUID,
    body: FinalizeSubmissionRequest,
    principal: StudentPrincipal,
    session: DbSession,
    idempotency_key: IdempotencyKey,
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
) -> SubmissionView:
    try:
        return await finalize_submission(
            session,
            principal=principal,
            submission_id=submission_id,
            version=body.version,
            confirm=body.confirm,
            idempotency_key=idempotency_key,
            correlation_id=request.state.correlation_id,
            settings=settings,
        )
    except InternshipError as exc:
        _raise(exc)
    raise AssertionError("unreachable")


@router.post("/assignments/{assignment_id}/resubmit", response_model=SubmissionView)
async def resubmit_route(
    assignment_id: uuid.UUID,
    body: ResubmissionRequest,
    principal: StudentPrincipal,
    session: DbSession,
    request: Request,
) -> SubmissionView:
    try:
        return await resubmit(
            session,
            principal=principal,
            assignment_id=assignment_id,
            body=body,
            correlation_id=request.state.correlation_id,
        )
    except InternshipError as exc:
        _raise(exc)
    raise AssertionError("unreachable")


@router.get("/feedback", response_model=list[FeedbackView])
async def feedback_route(principal: StudentPrincipal, session: DbSession) -> list[FeedbackView]:
    return await feedback(session, principal)


@router.get("/certificate-eligibility", response_model=CertificateEligibilityView)
async def certificate_route(
    principal: StudentPrincipal,
    session: DbSession,
    enrollment_id: uuid.UUID | None = None,
) -> CertificateEligibilityView:
    try:
        return await certificate_eligibility(session, principal, enrollment_id)
    except InternshipError as exc:
        _raise(exc)
    raise AssertionError("unreachable")


@router.post("/submissions/{submission_id}/ai-review", response_model=SubmissionAIReviewResponse)
async def ai_review_submission(
    submission_id: uuid.UUID,
    body: SubmissionAIReviewRequest,
    principal: StudentPrincipal,
    session: DbSession,
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
) -> SubmissionAIReviewResponse:
    try:
        return await review_submission_with_ai(
            session,
            principal=principal,
            submission_id=submission_id,
            body=body,
            settings=settings,
            correlation_id=request.state.correlation_id,
        )
    except InternshipError as exc:
        _raise(exc)
    raise AssertionError("unreachable")
