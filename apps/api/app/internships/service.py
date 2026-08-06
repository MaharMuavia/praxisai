import hashlib
import json
import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.service import FirebaseIdentityProvider, SessionPrincipal
from app.config import Settings
from app.domain.models import (
    AuditEvent,
    CohortEnrollment,
    CohortTrack,
    InternshipApplication,
    InternshipAssignmentTemplate,
    InternshipCertificate,
    InternshipCohort,
    InternshipCohortAssignment,
    InternshipPhase,
    InternshipProgram,
    InternshipReview,
    InternshipStudentAssignment,
    InternshipSubmission,
    InternshipTrack,
    InternshipTrackVersion,
    InternshipUnit,
    InternshipUnitCompletion,
    InternshipUpload,
    InternshipWeek,
    Organization,
    OrganizationMembership,
    StudentProfile,
    User,
)
from app.internships.policies import (
    evaluate_email_eligibility,
    is_application_complete,
    normalize_email,
)
from app.internships.reviews.scoring import RubricValidationError
from app.internships.reviews.scoring import weighted_score as score_rubric
from app.internships.schemas import (
    ApplicationDecisionRequest,
    ApplicationUpdate,
    ApplicationView,
    AssignmentView,
    CertificateEligibilityView,
    CohortSummary,
    CurriculumView,
    DashboardView,
    FeedbackView,
    ProgramDetail,
    ProgramSummary,
    PublicCertificateView,
    ResubmissionRequest,
    ReviewFinalizeRequest,
    ReviewQueueItem,
    SignupRequest,
    StartApplicationRequest,
    SubmissionDraftRequest,
    SubmissionView,
    TimelineItem,
    TrackSummary,
    UnitView,
    UploadCompleteRequest,
    UploadInitiateRequest,
    UploadView,
    WeekView,
)
from app.internships.storage import (
    LocalInternshipStorage,
    SupabaseInternshipStorage,
    SupabaseStorageError,
)
from app.internships.uploads.scanning import DemoScanner, DisabledProductionScanner


class InternshipError(ValueError):
    code = "internship_error"


class NotFound(InternshipError):
    code = "not_found"


class Forbidden(InternshipError):
    code = "permission_denied"


class Conflict(InternshipError):
    code = "record_changed"


class InvalidState(InternshipError):
    code = "invalid_state"


class ValidationFailure(InternshipError):
    code = "validation_error"


class StorageFailure(InternshipError):
    code = "storage_unavailable"


def now_utc() -> datetime:
    return datetime.now(UTC)


def _audit(
    session: AsyncSession,
    *,
    principal: SessionPrincipal | None,
    action: str,
    resource_type: str,
    resource_id: uuid.UUID | None,
    correlation_id: uuid.UUID,
    payload: dict[str, Any] | None = None,
) -> None:
    session.add(
        AuditEvent(
            actor_id=principal.user_id if principal else None,
            organization_id=principal.organization_id if principal else None,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            correlation_id=correlation_id,
            payload=payload or {},
        )
    )


def _track_summary(track: InternshipTrack, version: InternshipTrackVersion) -> TrackSummary:
    return TrackSummary(
        id=track.id,
        name=track.name,
        slug=track.slug,
        version_id=version.id,
        version=version.version,
        title=version.title,
        summary=version.summary,
        skill_outcomes=version.skill_outcomes,
        expected_weekly_hours=version.expected_weekly_hours,
    )


def _application_view(
    application: InternshipApplication,
    *,
    is_demo: bool,
) -> ApplicationView:
    return ApplicationView(
        id=application.id,
        program_id=application.program_id,
        cohort_id=application.cohort_id,
        applicant_user_id=application.applicant_user_id,
        status=application.status,
        version=application.version,
        primary_track_id=application.primary_track_id,
        secondary_track_id=application.secondary_track_id,
        education_status=application.education_status,
        degree_program=application.degree_program,
        country=application.country,
        timezone=application.timezone,
        weekly_availability_hours=application.weekly_availability_hours,
        technical_background=application.technical_background,
        motivation=application.motivation,
        portfolio_url=application.portfolio_url,
        github_url=application.github_url,
        linkedin_url=application.linkedin_url,
        submitted_at=application.submitted_at,
        decision_at=application.decision_at,
        decision_reason=application.decision_reason,
        is_demo=is_demo,
    )


async def list_programs(session: AsyncSession) -> list[ProgramSummary]:
    rows = (
        await session.execute(
            select(InternshipProgram)
            .where(InternshipProgram.status != "ARCHIVED")
            .order_by(InternshipProgram.name)
        )
    ).scalars()
    return [ProgramSummary.model_validate(row) for row in rows]


async def program_detail(session: AsyncSession, slug: str) -> ProgramDetail:
    program = await session.scalar(select(InternshipProgram).where(InternshipProgram.slug == slug))
    if program is None:
        raise NotFound("Program not found")
    cohorts = (
        await session.execute(
            select(InternshipCohort)
            .where(InternshipCohort.program_id == program.id)
            .order_by(InternshipCohort.starts_at)
        )
    ).scalars()
    track_rows = (
        await session.execute(
            select(InternshipTrack, InternshipTrackVersion)
            .join(InternshipTrackVersion, InternshipTrackVersion.track_id == InternshipTrack.id)
            .where(InternshipTrackVersion.status == "PUBLISHED")
            .order_by(InternshipTrack.name, InternshipTrackVersion.version.desc())
        )
    ).all()
    latest: dict[uuid.UUID, tuple[InternshipTrack, InternshipTrackVersion]] = {}
    for track, version in track_rows:
        latest.setdefault(track.id, (track, version))
    return ProgramDetail(
        **ProgramSummary.model_validate(program).model_dump(),
        cohorts=[CohortSummary.model_validate(row) for row in cohorts],
        tracks=[_track_summary(track, version) for track, version in latest.values()],
    )


async def signup(
    session: AsyncSession,
    *,
    body: SignupRequest,
    program_id: uuid.UUID,
    settings: Settings,
    correlation_id: uuid.UUID,
) -> tuple[str, uuid.UUID | None, SessionPrincipal | None]:
    identity = await FirebaseIdentityProvider(settings).verify(body.id_token)
    email = normalize_email(identity.email)
    cohort = await session.get(InternshipCohort, body.cohort_id)
    if cohort is None:
        raise NotFound("Cohort not found")
    program = await session.get(InternshipProgram, cohort.program_id)
    if (
        program is None
        or program.id != program_id
        or program.status not in {"APPLICATIONS_OPEN", "ACTIVE"}
    ):
        raise InvalidState("Applications are not open for this cohort")
    eligibility = await evaluate_email_eligibility(
        session, email=email, program=program, cohort=cohort
    )
    if not eligibility.eligible:
        raise Forbidden("This email is not eligible for the selected cohort")

    existing = await session.scalar(select(User).where(User.email == email))
    if existing is not None:
        # Keep the endpoint safe against account enumeration. Existing users can
        # use the normal Firebase session flow; no record details are disclosed.
        return "CHECK_EMAIL", None, None

    student_org = await session.scalar(
        select(Organization).where(Organization.slug == "praxisai-students")
    )
    if student_org is None:
        student_org = Organization(
            name="PraxisAI Student Community", slug="praxisai-students", kind="student_program"
        )
        session.add(student_org)
        await session.flush()
    user = User(
        email=email,
        display_name=email.split("@", 1)[0].replace(".", " ").title(),
        external_subject=identity.subject,
    )
    session.add(user)
    await session.flush()
    session.add_all(
        [
            OrganizationMembership(
                user_id=user.id,
                organization_id=student_org.id,
                role="student",
            ),
            StudentProfile(user_id=user.id),
        ]
    )
    application = InternshipApplication(
        applicant_user_id=user.id,
        program_id=program.id,
        cohort_id=cohort.id,
        status="ELIGIBILITY_REVIEW" if eligibility.requires_review else "DRAFT",
        email_verification_evidence={
            "provider": "firebase",
            "verified": True,
            "normalized_email": email,
            "eligibility_reason": eligibility.reason,
            "requires_review": eligibility.requires_review,
        },
        consent_snapshot={"terms_version": body.consent_version},
        correlation_id=correlation_id,
    )
    session.add(application)
    await session.flush()
    _audit(
        session,
        principal=SessionPrincipal(user.id, student_org.id, "student"),
        action="internship.account_provisioned",
        resource_type="internship_application",
        resource_id=application.id,
        correlation_id=correlation_id,
        payload={"email_eligibility": eligibility.reason},
    )
    await session.commit()
    principal = SessionPrincipal(user.id, student_org.id, "student")
    return "CREATED", application.id, principal


async def get_application(session: AsyncSession, principal: SessionPrincipal) -> ApplicationView:
    application = await session.scalar(
        select(InternshipApplication)
        .where(InternshipApplication.applicant_user_id == principal.user_id)
        .order_by(InternshipApplication.created_at.desc())
    )
    if application is None:
        raise NotFound("Internship application not found")
    program = await session.get(InternshipProgram, application.program_id)
    return _application_view(application, is_demo=bool(program and program.is_demo))


async def start_application(
    session: AsyncSession,
    *,
    principal: SessionPrincipal,
    body: StartApplicationRequest,
    correlation_id: uuid.UUID,
) -> ApplicationView:
    user = await session.get(User, principal.user_id)
    cohort = await session.get(InternshipCohort, body.cohort_id)
    program = await session.get(InternshipProgram, body.program_id)
    if user is None or cohort is None or program is None or cohort.program_id != program.id:
        raise NotFound("Program or cohort not found")
    if program.status not in {"APPLICATIONS_OPEN", "ACTIVE"} or cohort.status not in {
        "APPLICATIONS_OPEN",
        "ACTIVE",
    }:
        raise InvalidState("Applications are not open for this cohort")
    eligibility = await evaluate_email_eligibility(
        session, email=user.email, program=program, cohort=cohort
    )
    if not eligibility.eligible:
        raise Forbidden("This email is not eligible for the selected cohort")
    active_statuses = {"DRAFT", "ELIGIBILITY_REVIEW", "SUBMITTED", "WAITLISTED", "ACCEPTED"}
    existing = await session.scalar(
        select(InternshipApplication)
        .where(
            InternshipApplication.applicant_user_id == principal.user_id,
            InternshipApplication.cohort_id == cohort.id,
            InternshipApplication.status.in_(active_statuses),
        )
        .with_for_update()
    )
    if existing is not None:
        raise Conflict("An active application already exists for this cohort")
    application = InternshipApplication(
        applicant_user_id=principal.user_id,
        program_id=program.id,
        cohort_id=cohort.id,
        status="ELIGIBILITY_REVIEW" if eligibility.requires_review else "DRAFT",
        university_id=eligibility.university_id,
        email_verification_evidence={
            "provider": "existing_authenticated_session",
            "verified": True,
            "normalized_email": normalize_email(user.email),
            "eligibility_reason": eligibility.reason,
            "requires_review": eligibility.requires_review,
        },
        consent_snapshot={"terms_version": body.consent_version},
        correlation_id=correlation_id,
    )
    session.add(application)
    await session.flush()
    _audit(
        session,
        principal=principal,
        action="internship.application_started",
        resource_type="internship_application",
        resource_id=application.id,
        correlation_id=correlation_id,
        payload={"eligibility_reason": eligibility.reason},
    )
    await session.commit()
    return _application_view(application, is_demo=program.is_demo)


async def update_application(
    session: AsyncSession,
    *,
    principal: SessionPrincipal,
    body: ApplicationUpdate,
    correlation_id: uuid.UUID,
) -> ApplicationView:
    application = await session.scalar(
        select(InternshipApplication)
        .where(InternshipApplication.applicant_user_id == principal.user_id)
        .with_for_update()
    )
    if application is None:
        raise NotFound("Internship application not found")
    if application.status not in {"DRAFT", "ELIGIBILITY_REVIEW"}:
        raise InvalidState("Submitted applications require an explicit correction request")
    if application.version != body.version:
        raise Conflict("Application changed; reload before saving")
    for field, value in body.model_dump(exclude={"version"}).items():
        setattr(application, field, str(value) if field.endswith("_url") and value else value)
    application.version += 1
    _audit(
        session,
        principal=principal,
        action="internship.application_updated",
        resource_type="internship_application",
        resource_id=application.id,
        correlation_id=correlation_id,
    )
    await session.commit()
    program = await session.get(InternshipProgram, application.program_id)
    return _application_view(application, is_demo=bool(program and program.is_demo))


async def submit_application(
    session: AsyncSession,
    *,
    principal: SessionPrincipal,
    version: int,
    consent_version: str,
    idempotency_key: str,
    correlation_id: uuid.UUID,
) -> ApplicationView:
    application = await session.scalar(
        select(InternshipApplication)
        .where(InternshipApplication.applicant_user_id == principal.user_id)
        .with_for_update()
    )
    if application is None:
        raise NotFound("Internship application not found")
    if application.submit_idempotency_key == idempotency_key:
        program = await session.get(InternshipProgram, application.program_id)
        return _application_view(application, is_demo=bool(program and program.is_demo))
    if application.status not in {"DRAFT", "ELIGIBILITY_REVIEW"}:
        raise InvalidState("Application has already been submitted")
    if application.version != version:
        raise Conflict("Application changed; reload before submitting")
    if not is_application_complete(application):
        raise ValidationFailure("Application is incomplete")
    application.status = "SUBMITTED"
    application.submitted_at = now_utc()
    application.submit_idempotency_key = idempotency_key
    application.consent_snapshot = {"terms_version": consent_version}
    application.version += 1
    _audit(
        session,
        principal=principal,
        action="internship.application_submitted",
        resource_type="internship_application",
        resource_id=application.id,
        correlation_id=correlation_id,
    )
    await session.commit()
    program = await session.get(InternshipProgram, application.program_id)
    return _application_view(application, is_demo=bool(program and program.is_demo))


async def decide_application(
    session: AsyncSession,
    *,
    application_id: uuid.UUID,
    principal: SessionPrincipal,
    body: ApplicationDecisionRequest,
    correlation_id: uuid.UUID,
) -> ApplicationView:
    application = await session.scalar(
        select(InternshipApplication)
        .where(InternshipApplication.id == application_id)
        .with_for_update()
    )
    if application is None:
        raise NotFound("Application not found")
    if application.version != body.expected_version:
        raise Conflict("Application changed; reload before deciding")
    if application.status not in {"SUBMITTED", "ELIGIBILITY_REVIEW", "WAITLISTED"}:
        raise InvalidState("Application is not awaiting a decision")
    assigned_track_version_id = body.track_version_id
    if body.decision == "ACCEPTED":
        if assigned_track_version_id is None:
            raise ValidationFailure("Acceptance requires an assigned track version")
        cohort = await session.scalar(
            select(InternshipCohort)
            .where(InternshipCohort.id == application.cohort_id)
            .with_for_update()
        )
        if cohort is None:
            raise NotFound("Cohort not found")
        cohort_track = await session.scalar(
            select(CohortTrack)
            .where(
                CohortTrack.cohort_id == application.cohort_id,
                CohortTrack.track_version_id == assigned_track_version_id,
            )
            .with_for_update()
        )
        if cohort_track is None:
            raise ValidationFailure("Assigned track is not available in this cohort")
        active_statuses = ["INVITED", "ENROLLED", "ACTIVE", "COMPLETED"]
        cohort_count = await session.scalar(
            select(func.count(CohortEnrollment.id)).where(
                CohortEnrollment.cohort_id == cohort.id,
                CohortEnrollment.status.in_(active_statuses),
            )
        )
        if (cohort_count or 0) >= cohort.capacity:
            raise Conflict("Cohort capacity is full")
        assigned_count = await session.scalar(
            select(func.count(CohortEnrollment.id)).where(
                CohortEnrollment.cohort_id == application.cohort_id,
                CohortEnrollment.track_version_id == assigned_track_version_id,
                CohortEnrollment.status.in_(active_statuses),
            )
        )
        if assigned_count and assigned_count >= cohort_track.capacity:
            raise Conflict("Track capacity is full")
        enrollment = await session.scalar(
            select(CohortEnrollment).where(
                CohortEnrollment.cohort_id == application.cohort_id,
                CohortEnrollment.student_user_id == application.applicant_user_id,
            )
        )
        if enrollment is None:
            session.add(
                CohortEnrollment(
                    cohort_id=application.cohort_id,
                    student_user_id=application.applicant_user_id,
                    track_version_id=assigned_track_version_id,
                    status="ENROLLED",
                )
            )
        elif enrollment.track_version_id != assigned_track_version_id:
            raise Conflict("Enrollment track is immutable")
    application.status = body.decision
    application.decision_reason = body.reason
    application.decision_at = now_utc()
    application.reviewer_id = principal.user_id
    application.version += 1
    _audit(
        session,
        principal=principal,
        action="internship.application_decided",
        resource_type="internship_application",
        resource_id=application.id,
        correlation_id=correlation_id,
        payload={"decision": body.decision},
    )
    await session.commit()
    program = await session.get(InternshipProgram, application.program_id)
    return _application_view(application, is_demo=bool(program and program.is_demo))


async def _enrollment(session: AsyncSession, principal: SessionPrincipal) -> CohortEnrollment:
    enrollment = await session.scalar(
        select(CohortEnrollment)
        .where(
            CohortEnrollment.student_user_id == principal.user_id,
            CohortEnrollment.status.not_in(["WITHDRAWN", "TERMINATED"]),
        )
        .order_by(CohortEnrollment.created_at.desc())
    )
    if enrollment is None:
        raise NotFound("Internship enrollment not found")
    return enrollment


async def dashboard(session: AsyncSession, principal: SessionPrincipal) -> DashboardView:
    try:
        enrollment = await _enrollment(session, principal)
    except NotFound:
        return DashboardView(
            enrollment_id=None,
            program_name=None,
            cohort_name=None,
            track=None,
            enrollment_status=None,
            certificate_eligibility=None,
            completed_units=0,
            required_units=0,
            passed_assignments=0,
            required_assignments=0,
            progress_percent=0,
            timeline=[],
            is_demo=False,
        )
    cohort = await session.get(InternshipCohort, enrollment.cohort_id)
    program = await session.get(InternshipProgram, cohort.program_id) if cohort else None
    version = await session.get(InternshipTrackVersion, enrollment.track_version_id)
    track = await session.get(InternshipTrack, version.track_id) if version else None
    unit_total = await session.scalar(
        select(func.count(InternshipUnit.id))
        .join(InternshipWeek, InternshipWeek.id == InternshipUnit.week_id)
        .join(InternshipPhase, InternshipPhase.id == InternshipWeek.phase_id)
        .join(CohortTrack, CohortTrack.id == InternshipPhase.cohort_track_id)
        .where(CohortTrack.track_version_id == enrollment.track_version_id)
    )
    completed_units = await session.scalar(
        select(func.count(InternshipUnitCompletion.id)).where(
            InternshipUnitCompletion.enrollment_id == enrollment.id
        )
    )
    assignment_total = await session.scalar(
        select(func.count(InternshipStudentAssignment.id)).where(
            InternshipStudentAssignment.student_user_id == principal.user_id
        )
    )
    passed_assignments = await session.scalar(
        select(func.count(InternshipStudentAssignment.id)).where(
            InternshipStudentAssignment.student_user_id == principal.user_id,
            InternshipStudentAssignment.final_result == "PASS",
        )
    )
    required = (unit_total or 0) + (assignment_total or 0)
    done = (completed_units or 0) + (passed_assignments or 0)
    application = await session.scalar(
        select(InternshipApplication)
        .where(InternshipApplication.applicant_user_id == principal.user_id)
        .order_by(InternshipApplication.created_at.desc())
    )
    application_state = {
        "DRAFT": "IN_PROGRESS",
        "ELIGIBILITY_REVIEW": "IN_PROGRESS",
        "SUBMITTED": "AWAITING_DECISION",
        "WAITLISTED": "WAITLISTED",
        "ACCEPTED": "COMPLETE",
        "REJECTED": "REJECTED",
    }.get(application.status if application else "", "NOT_STARTED")
    admission_state = (
        "COMPLETE"
        if application and application.status == "ACCEPTED"
        else "REJECTED"
        if application and application.status == "REJECTED"
        else "AWAITING_DECISION"
        if application and application.status in {"SUBMITTED", "WAITLISTED"}
        else "NOT_STARTED"
    )
    timeline = [
        TimelineItem(label="Application", state=application_state),
        TimelineItem(label="Admission", state=admission_state),
    ]
    if cohort:
        phases = (
            await session.execute(
                select(InternshipPhase)
                .join(CohortTrack, CohortTrack.id == InternshipPhase.cohort_track_id)
                .where(CohortTrack.track_version_id == enrollment.track_version_id)
                .order_by(InternshipPhase.ordinal)
            )
        ).scalars()
        now = now_utc()
        timeline.extend(
            TimelineItem(
                label=phase.name,
                state=(
                    "CURRENT"
                    if phase.starts_at <= now <= phase.ends_at
                    else "UPCOMING"
                    if now < phase.starts_at
                    else "COMPLETE"
                ),
                starts_at=phase.starts_at,
                ends_at=phase.ends_at,
            )
            for phase in phases
        )
    assignment_rows = (
        await session.execute(
            select(
                InternshipStudentAssignment,
                InternshipCohortAssignment,
                InternshipAssignmentTemplate,
            )
            .join(
                InternshipCohortAssignment,
                InternshipCohortAssignment.id == InternshipStudentAssignment.cohort_assignment_id,
            )
            .join(
                InternshipAssignmentTemplate,
                InternshipAssignmentTemplate.id == InternshipCohortAssignment.template_id,
            )
            .where(InternshipStudentAssignment.student_user_id == principal.user_id)
        )
    ).all()
    timeline.extend(
        TimelineItem(
            label=f"Assignment: {template.title}",
            state=assignment.state,
            starts_at=cohort_assignment.release_at,
            ends_at=assignment.due_at or cohort_assignment.deadline,
        )
        for assignment, cohort_assignment, template in assignment_rows
    )
    timeline.append(TimelineItem(label="Completion", state=enrollment.certificate_eligibility))
    certificate = await session.scalar(
        select(InternshipCertificate).where(InternshipCertificate.enrollment_id == enrollment.id)
    )
    timeline.append(
        TimelineItem(label="Credential", state=certificate.state if certificate else "NOT_ISSUED")
    )
    return DashboardView(
        enrollment_id=enrollment.id,
        program_name=program.name if program else None,
        cohort_name=cohort.name if cohort else None,
        track=_track_summary(track, version) if track and version else None,
        enrollment_status=enrollment.status,
        certificate_eligibility=enrollment.certificate_eligibility,
        completed_units=completed_units or 0,
        required_units=unit_total or 0,
        passed_assignments=passed_assignments or 0,
        required_assignments=assignment_total or 0,
        progress_percent=round(done * 100 / required) if required else 0,
        timeline=timeline,
        is_demo=bool(program and program.is_demo),
    )


async def curriculum(session: AsyncSession, principal: SessionPrincipal) -> CurriculumView:
    enrollment = await _enrollment(session, principal)
    version = await session.get(InternshipTrackVersion, enrollment.track_version_id)
    if version is None:
        raise NotFound("Track version not found")
    track = await session.get(InternshipTrack, version.track_id)
    if track is None:
        raise NotFound("Track not found")
    weeks = (
        await session.execute(
            select(InternshipWeek)
            .join(InternshipPhase, InternshipPhase.id == InternshipWeek.phase_id)
            .join(CohortTrack, CohortTrack.id == InternshipPhase.cohort_track_id)
            .where(CohortTrack.track_version_id == version.id)
            .order_by(InternshipWeek.week_number)
        )
    ).scalars()
    completed_ids = set(
        (
            await session.execute(
                select(InternshipUnitCompletion.unit_id).where(
                    InternshipUnitCompletion.enrollment_id == enrollment.id
                )
            )
        ).scalars()
    )
    now = now_utc()
    week_views: list[WeekView] = []
    for week in weeks:
        units = (
            await session.execute(
                select(InternshipUnit)
                .where(InternshipUnit.week_id == week.id)
                .order_by(InternshipUnit.ordinal)
            )
        ).scalars()
        week_views.append(
            WeekView(
                id=week.id,
                week_number=week.week_number,
                title=week.title,
                summary=week.summary,
                starts_at=week.starts_at,
                ends_at=week.ends_at,
                required_unit_count=week.required_unit_count,
                required_assignment_count=week.required_assignment_count,
                unlocked=now >= week.starts_at,
                units=[
                    UnitView(
                        id=unit.id,
                        week_id=unit.week_id,
                        ordinal=unit.ordinal,
                        unit_type=unit.unit_type,
                        title=unit.title,
                        summary=unit.summary,
                        objectives=unit.objectives,
                        resources=unit.resources,
                        practical_exercise=unit.practical_exercise,
                        completion_rule=unit.completion_rule,
                        prerequisites=unit.prerequisites,
                        release_at=unit.release_at,
                        deadline=unit.deadline,
                        is_required=unit.is_required,
                        completed=unit.id in completed_ids,
                    )
                    for unit in units
                ],
            )
        )
    return CurriculumView(track=_track_summary(track, version), weeks=week_views)


async def complete_unit(
    session: AsyncSession,
    *,
    principal: SessionPrincipal,
    unit_id: uuid.UUID,
    evidence: dict[str, Any],
    correlation_id: uuid.UUID,
) -> CurriculumView:
    enrollment = await _enrollment(session, principal)
    unit = await session.get(InternshipUnit, unit_id)
    if unit is None:
        raise NotFound("Learning unit not found")
    week = await session.get(InternshipWeek, unit.week_id)
    if week is None:
        raise NotFound("Learning week not found")
    phase = await session.get(InternshipPhase, week.phase_id) if week else None
    cohort_track = await session.get(CohortTrack, phase.cohort_track_id) if phase else None
    if cohort_track is None or cohort_track.track_version_id != enrollment.track_version_id:
        raise NotFound("Learning unit not found")
    if now_utc() < (unit.release_at or week.starts_at):
        raise InvalidState("Learning unit is locked")
    existing = await session.scalar(
        select(InternshipUnitCompletion).where(
            InternshipUnitCompletion.enrollment_id == enrollment.id,
            InternshipUnitCompletion.unit_id == unit.id,
        )
    )
    if existing is None:
        session.add(
            InternshipUnitCompletion(
                enrollment_id=enrollment.id,
                unit_id=unit.id,
                evidence=evidence,
                completed_at=now_utc(),
            )
        )
        _audit(
            session,
            principal=principal,
            action="internship.learning_unit_completed",
            resource_type="internship_unit",
            resource_id=unit.id,
            correlation_id=correlation_id,
        )
        await session.commit()
    return await curriculum(session, principal)


async def _assignment_view(
    session: AsyncSession, assignment: InternshipStudentAssignment
) -> AssignmentView:
    cohort_assignment = await session.get(
        InternshipCohortAssignment, assignment.cohort_assignment_id
    )
    if cohort_assignment is None:
        raise NotFound("Assignment not found")
    template = await session.get(InternshipAssignmentTemplate, cohort_assignment.template_id)
    if template is None:
        raise NotFound("Assignment template not found")
    now = now_utc()
    state = assignment.state
    if state == "LOCKED" and now >= cohort_assignment.release_at:
        state = "AVAILABLE"
    return AssignmentView(
        id=assignment.id,
        title=template.title,
        summary=template.summary,
        problem_statement=template.problem_statement,
        objectives=template.objectives,
        deliverables=template.deliverables,
        acceptance_criteria=template.acceptance_criteria,
        required_artifact_types=template.required_artifact_types,
        rubric=template.rubric,
        pass_score=template.pass_score,
        state=state,
        release_at=cohort_assignment.release_at,
        due_at=assignment.due_at or cohort_assignment.deadline,
        submitted_at=assignment.submitted_at,
        attempt_count=assignment.attempt_count,
        current_submission_id=assignment.current_submission_id,
        is_late=now > (assignment.due_at or cohort_assignment.deadline),
    )


async def list_assignments(
    session: AsyncSession, principal: SessionPrincipal
) -> list[AssignmentView]:
    rows = (
        await session.execute(
            select(InternshipStudentAssignment)
            .where(InternshipStudentAssignment.student_user_id == principal.user_id)
            .order_by(InternshipStudentAssignment.created_at)
        )
    ).scalars()
    return [await _assignment_view(session, row) for row in rows]


async def get_assignment(
    session: AsyncSession, *, principal: SessionPrincipal, assignment_id: uuid.UUID
) -> InternshipStudentAssignment:
    assignment = await session.scalar(
        select(InternshipStudentAssignment).where(
            InternshipStudentAssignment.id == assignment_id,
            InternshipStudentAssignment.student_user_id == principal.user_id,
        )
    )
    if assignment is None:
        raise NotFound("Assignment not found")
    return assignment


async def start_assignment(
    session: AsyncSession,
    *,
    principal: SessionPrincipal,
    assignment_id: uuid.UUID,
    correlation_id: uuid.UUID,
) -> AssignmentView:
    assignment = await get_assignment(session, principal=principal, assignment_id=assignment_id)
    cohort_assignment = await session.get(
        InternshipCohortAssignment, assignment.cohort_assignment_id
    )
    if cohort_assignment is None:
        raise NotFound("Assignment not found")
    if now_utc() < cohort_assignment.release_at:
        raise InvalidState("Assignment is locked")
    if assignment.state == "LOCKED":
        assignment.state = "AVAILABLE"
    if assignment.state not in {"AVAILABLE", "IN_PROGRESS", "CHANGES_REQUESTED"}:
        raise InvalidState("Assignment cannot be started in its current state")
    assignment.state = "IN_PROGRESS"
    assignment.started_at = assignment.started_at or now_utc()
    _audit(
        session,
        principal=principal,
        action="internship.assignment_started",
        resource_type="internship_student_assignment",
        resource_id=assignment.id,
        correlation_id=correlation_id,
    )
    await session.commit()
    return await _assignment_view(session, assignment)


async def create_submission_draft(
    session: AsyncSession,
    *,
    principal: SessionPrincipal,
    assignment_id: uuid.UUID,
    body: SubmissionDraftRequest,
    correlation_id: uuid.UUID,
) -> SubmissionView:
    assignment = await get_assignment(session, principal=principal, assignment_id=assignment_id)
    if assignment.state in {"LOCKED", "PASSED", "FAILED", "WITHDRAWN"}:
        raise InvalidState("Assignment is not accepting a draft")
    if assignment.current_submission_id:
        current = await session.get(InternshipSubmission, assignment.current_submission_id)
        if current and current.state == "DRAFT":
            current.links = {key: str(value) for key, value in body.links.items()}
            current.text_fields = body.text_fields
            current.artifact_upload_ids = body.artifact_upload_ids
            await session.commit()
            return SubmissionView.model_validate(current)
    max_version = await session.scalar(
        select(func.max(InternshipSubmission.version)).where(
            InternshipSubmission.student_assignment_id == assignment.id
        )
    )
    submission = InternshipSubmission(
        student_assignment_id=assignment.id,
        student_user_id=principal.user_id,
        state="DRAFT",
        version=(max_version or 0) + 1,
        links={key: str(value) for key, value in body.links.items()},
        text_fields=body.text_fields,
        artifact_upload_ids=body.artifact_upload_ids,
        correlation_id=correlation_id,
    )
    session.add(submission)
    await session.flush()
    assignment.current_submission_id = submission.id
    await session.commit()
    return SubmissionView.model_validate(submission)


async def save_submission(
    session: AsyncSession,
    *,
    principal: SessionPrincipal,
    submission_id: uuid.UUID,
    body: SubmissionDraftRequest,
) -> SubmissionView:
    submission = await session.scalar(
        select(InternshipSubmission).where(
            InternshipSubmission.id == submission_id,
            InternshipSubmission.student_user_id == principal.user_id,
        )
    )
    if submission is None:
        raise NotFound("Submission not found")
    if submission.state != "DRAFT":
        raise InvalidState("Finalized submissions are immutable")
    submission.links = {key: str(value) for key, value in body.links.items()}
    submission.text_fields = body.text_fields
    submission.artifact_upload_ids = body.artifact_upload_ids
    await session.commit()
    return SubmissionView.model_validate(submission)


async def get_submission(
    session: AsyncSession, *, principal: SessionPrincipal, submission_id: uuid.UUID
) -> SubmissionView:
    submission = await session.scalar(
        select(InternshipSubmission).where(
            InternshipSubmission.id == submission_id,
            InternshipSubmission.student_user_id == principal.user_id,
        )
    )
    if submission is None:
        raise NotFound("Submission not found")
    return SubmissionView.model_validate(submission)


def _submission_hash(submission: InternshipSubmission) -> str:
    payload = {
        "assignment_id": str(submission.student_assignment_id),
        "version": submission.version,
        "links": submission.links,
        "text_fields": submission.text_fields,
        "artifact_upload_ids": sorted(submission.artifact_upload_ids),
        "artifact_snapshot": submission.artifact_snapshot,
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


async def finalize_submission(
    session: AsyncSession,
    *,
    principal: SessionPrincipal,
    submission_id: uuid.UUID,
    version: int,
    confirm: bool,
    idempotency_key: str,
    correlation_id: uuid.UUID,
    settings: Settings,
) -> SubmissionView:
    submission = await session.scalar(
        select(InternshipSubmission)
        .where(
            InternshipSubmission.id == submission_id,
            InternshipSubmission.student_user_id == principal.user_id,
        )
        .with_for_update()
    )
    if submission is None:
        raise NotFound("Submission not found")
    if submission.finalize_idempotency_key == idempotency_key:
        return SubmissionView.model_validate(submission)
    if not confirm:
        raise ValidationFailure("Final submission requires confirmation")
    if submission.state != "DRAFT":
        raise InvalidState("Submission has already been finalized")
    if submission.version != version:
        raise Conflict("Submission changed; reload before finalizing")
    assignment = await session.get(InternshipStudentAssignment, submission.student_assignment_id)
    if assignment is None:
        raise NotFound("Assignment not found")
    cohort_assignment = await session.get(
        InternshipCohortAssignment, assignment.cohort_assignment_id
    )
    template = await session.get(
        InternshipAssignmentTemplate, cohort_assignment.template_id if cohort_assignment else None
    )
    if template is None or cohort_assignment is None:
        raise NotFound("Assignment template not found")
    upload_ids = list(dict.fromkeys(submission.artifact_upload_ids))
    uploads = list(
        (
            await session.execute(
                select(InternshipUpload).where(
                    InternshipUpload.upload_id.in_(upload_ids),
                    InternshipUpload.owner_user_id == principal.user_id,
                    InternshipUpload.student_assignment_id == assignment.id,
                )
            )
        ).scalars()
    )
    uploads_by_id = {upload.upload_id: upload for upload in uploads}
    if len(uploads_by_id) != len(upload_ids):
        raise ValidationFailure("Submission references an unknown or unrelated upload")
    maximum_package_size = 250 * 1024 * 1024
    if sum(upload.size_bytes for upload in uploads) > maximum_package_size:
        raise ValidationFailure("Submission package exceeds the aggregate size limit")
    for upload in uploads:
        if upload.state != "CLEAN" or now_utc() >= upload.expires_at:
            raise ValidationFailure("Every referenced upload must be clean and unexpired")
        try:
            if settings.storage_provider == "supabase":
                stored = await SupabaseInternshipStorage(settings).read(upload.storage_key)
            else:
                stored = LocalInternshipStorage(settings.internship_local_storage_path).read(
                    upload.storage_key
                )
        except (SupabaseStorageError, OSError) as exc:
            raise StorageFailure("Referenced upload is not available in storage") from exc
        if hashlib.sha256(stored).hexdigest() != upload.sha256:
            raise ValidationFailure("Referenced upload hash no longer matches storage")
    artifact_types = {upload.artifact_type for upload in uploads}
    allowed_types = {
        str(item.get("type")) for item in template.required_artifact_types if item.get("type")
    }
    if any(upload.artifact_type not in allowed_types for upload in uploads):
        raise ValidationFailure(
            "Submission contains an artifact type not allowed by the assignment"
        )
    missing = []
    for item in template.required_artifact_types:
        artifact_type = str(item.get("type", "artifact"))
        if not item.get("required", True):
            continue
        supplied = (
            artifact_type in artifact_types
            or artifact_type in submission.links
            or artifact_type in submission.text_fields
        )
        if not supplied:
            missing.append(artifact_type)
    if missing:
        raise ValidationFailure("Missing required artifacts: " + ", ".join(missing))
    submission.artifact_snapshot = [
        {
            "upload_id": upload.upload_id,
            "artifact_type": upload.artifact_type,
            "filename": upload.filename,
            "size_bytes": upload.size_bytes,
            "content_type": upload.content_type,
            "sha256": upload.sha256,
        }
        for upload in sorted(uploads, key=lambda row: row.upload_id)
    ]
    submission.state = "FINALIZED"
    submission.canonical_hash = _submission_hash(submission)
    submission.rubric_version = template.version
    submission.submitted_at = now_utc()
    submission.deadline_status = (
        "LATE" if submission.submitted_at > cohort_assignment.deadline else "ON_TIME"
    )
    submission.finalize_idempotency_key = idempotency_key
    assignment.state = "UNDER_REVIEW"
    assignment.submitted_at = submission.submitted_at
    assignment.attempt_count += 1
    for upload in uploads:
        upload.state = "ATTACHED"
    session.add(
        InternshipReview(
            student_assignment_id=assignment.id,
            submission_id=submission.id,
            reviewer_id=None,
            status="UNASSIGNED",
        )
    )
    _audit(
        session,
        principal=principal,
        action="internship.submission_finalized",
        resource_type="internship_submission",
        resource_id=submission.id,
        correlation_id=correlation_id,
        payload={"version": submission.version, "deadline_status": submission.deadline_status},
    )
    await session.commit()
    return SubmissionView.model_validate(submission)


async def resubmit(
    session: AsyncSession,
    *,
    principal: SessionPrincipal,
    assignment_id: uuid.UUID,
    body: ResubmissionRequest,
    correlation_id: uuid.UUID,
) -> SubmissionView:
    assignment = await get_assignment(session, principal=principal, assignment_id=assignment_id)
    if assignment.state != "CHANGES_REQUESTED":
        raise InvalidState("Resubmission is available only after changes are requested")
    cohort_assignment = await session.get(
        InternshipCohortAssignment, assignment.cohort_assignment_id
    )
    template = await session.get(
        InternshipAssignmentTemplate, cohort_assignment.template_id if cohort_assignment else None
    )
    cohort_track = await session.get(
        CohortTrack, cohort_assignment.cohort_track_id if cohort_assignment else None
    )
    cohort = await session.get(InternshipCohort, cohort_track.cohort_id if cohort_track else None)
    policy = (template.resubmission_policy if template else {}) or (
        cohort.resubmission_policy if cohort else {}
    )
    max_attempts = policy.get("max_attempts")
    if not isinstance(max_attempts, int) or max_attempts < 1:
        raise InvalidState("Resubmission policy is not configured")
    if assignment.attempt_count >= max_attempts:
        raise InvalidState("Maximum submission attempts reached")
    if assignment.due_at and now_utc() > assignment.due_at:
        raise InvalidState("Resubmission deadline has passed")
    previous = await session.get(InternshipSubmission, assignment.current_submission_id)
    if previous is None:
        raise NotFound("Previous submission not found")
    competing_draft = await session.scalar(
        select(InternshipSubmission).where(
            InternshipSubmission.student_assignment_id == assignment.id,
            InternshipSubmission.state == "DRAFT",
        )
    )
    if competing_draft is not None:
        raise Conflict("A resubmission draft already exists")
    max_version = await session.scalar(
        select(func.max(InternshipSubmission.version)).where(
            InternshipSubmission.student_assignment_id == assignment.id
        )
    )
    submission = InternshipSubmission(
        student_assignment_id=assignment.id,
        student_user_id=principal.user_id,
        state="DRAFT",
        version=(max_version or 0) + 1,
        previous_submission_id=previous.id,
        change_summary=body.change_summary,
        correlation_id=correlation_id,
    )
    session.add(submission)
    await session.flush()
    assignment.current_submission_id = submission.id
    assignment.state = "RESUBMITTED"
    await session.commit()
    return SubmissionView.model_validate(submission)


async def feedback(session: AsyncSession, principal: SessionPrincipal) -> list[FeedbackView]:
    rows = (
        await session.execute(
            select(InternshipReview)
            .where(
                InternshipReview.reviewer_id.is_not(None),
                InternshipReview.status == "FINALIZED",
                InternshipReview.student_assignment_id.in_(
                    select(InternshipStudentAssignment.id).where(
                        InternshipStudentAssignment.student_user_id == principal.user_id
                    )
                ),
            )
            .order_by(InternshipReview.finalized_at.desc())
        )
    ).scalars()
    return [
        FeedbackView(
            review_id=row.id,
            assignment_id=row.student_assignment_id,
            submission_id=row.submission_id,
            decision=row.decision or "PENDING",
            weighted_total=row.weighted_total or 0,
            student_feedback=row.student_feedback or "",
            finalized_at=row.finalized_at or row.updated_at,
        )
        for row in rows
    ]


async def certificate_eligibility(
    session: AsyncSession, principal: SessionPrincipal
) -> CertificateEligibilityView:
    try:
        enrollment = await _enrollment(session, principal)
    except NotFound:
        return CertificateEligibilityView(
            enrollment_id=None,
            state="NOT_ELIGIBLE",
            reason="No active enrollment",
            certificate_id=None,
            public_slug=None,
        )
    certificate = await session.scalar(
        select(InternshipCertificate).where(InternshipCertificate.enrollment_id == enrollment.id)
    )
    reason = "Complete all required learning units and pass every assignment"
    if enrollment.certificate_eligibility == "ELIGIBLE":
        reason = "All deterministic completion gates passed; coordinator approval is required"
    elif enrollment.certificate_eligibility == "APPROVED":
        reason = "Completion was approved by a coordinator; credential issuance is available"
    elif enrollment.certificate_eligibility == "REJECTED":
        reason = "Completion was rejected; the student may follow the appeal path"
    return CertificateEligibilityView(
        enrollment_id=enrollment.id,
        state=certificate.state if certificate else enrollment.certificate_eligibility,
        reason=reason,
        certificate_id=certificate.id if certificate else None,
        public_slug=certificate.public_slug if certificate else None,
    )


async def decide_completion(
    session: AsyncSession,
    *,
    enrollment_id: uuid.UUID,
    principal: SessionPrincipal,
    decision: str,
    reason: str,
    correlation_id: uuid.UUID,
) -> CertificateEligibilityView:
    enrollment = await session.scalar(
        select(CohortEnrollment).where(CohortEnrollment.id == enrollment_id).with_for_update()
    )
    if enrollment is None:
        raise NotFound("Enrollment not found")
    if decision == "APPROVED" and enrollment.certificate_eligibility != "ELIGIBLE":
        raise InvalidState("Completion approval requires deterministic eligibility")
    if decision == "REJECTED" and not reason.strip():
        raise ValidationFailure("Completion rejection requires a reason")
    enrollment.certificate_eligibility = decision
    enrollment.version += 1
    _audit(
        session,
        principal=principal,
        action="internship.completion_decided",
        resource_type="internship_cohort_enrollment",
        resource_id=enrollment.id,
        correlation_id=correlation_id,
        payload={"decision": decision},
    )
    await session.commit()
    return await certificate_eligibility(
        session,
        SessionPrincipal(principal.user_id, principal.organization_id, "student"),
    )


async def list_operations_applications(
    session: AsyncSession, *, limit: int, offset: int
) -> list[Any]:
    rows = (
        await session.execute(
            select(InternshipApplication, User)
            .join(User, User.id == InternshipApplication.applicant_user_id)
            .order_by(InternshipApplication.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
    ).all()
    from app.internships.schemas import OperationsApplicationView

    output = []
    for application, user in rows:
        program = await session.get(InternshipProgram, application.program_id)
        output.append(
            OperationsApplicationView(
                **_application_view(
                    application, is_demo=bool(program and program.is_demo)
                ).model_dump(),
                applicant_display_name=user.display_name,
                applicant_email=user.email,
            )
        )
    return output


async def review_queue(
    session: AsyncSession,
    *,
    limit: int,
    offset: int,
    principal: SessionPrincipal | None = None,
    review_id: uuid.UUID | None = None,
) -> list[ReviewQueueItem]:
    assigned_only = principal is not None and principal.role in {"reviewer", "technical_lead"}
    filters = (
        [InternshipReview.reviewer_id == principal.user_id] if assigned_only and principal else []
    )
    if review_id is not None:
        filters.append(InternshipReview.id == review_id)
    rows = (
        await session.execute(
            select(
                InternshipReview,
                InternshipStudentAssignment,
                InternshipSubmission,
                User,
                InternshipAssignmentTemplate,
            )
            .join(
                InternshipStudentAssignment,
                InternshipStudentAssignment.id == InternshipReview.student_assignment_id,
            )
            .join(InternshipSubmission, InternshipSubmission.id == InternshipReview.submission_id)
            .join(User, User.id == InternshipStudentAssignment.student_user_id)
            .join(
                InternshipCohortAssignment,
                InternshipCohortAssignment.id == InternshipStudentAssignment.cohort_assignment_id,
            )
            .join(
                InternshipAssignmentTemplate,
                InternshipAssignmentTemplate.id == InternshipCohortAssignment.template_id,
            )
            .where(*filters)
            .order_by(InternshipReview.created_at)
            .limit(limit)
            .offset(offset)
        )
    ).all()
    return [
        ReviewQueueItem(
            review_id=review.id,
            assignment_id=assignment.id,
            submission_id=submission.id,
            student_display_name=user.display_name,
            assignment_title=template.title,
            status=review.status,
            version=submission.version,
        )
        for review, assignment, submission, user, template in rows
    ]


def weighted_score(scores: list[dict[str, Any]], rubric: list[dict[str, Any]]) -> int:
    try:
        return score_rubric(scores, rubric)
    except RubricValidationError as exc:
        raise ValidationFailure(str(exc)) from exc


async def _refresh_certificate_eligibility(
    session: AsyncSession, *, student_assignment: InternshipStudentAssignment
) -> None:
    cohort_assignment = await session.get(
        InternshipCohortAssignment, student_assignment.cohort_assignment_id
    )
    if cohort_assignment is None:
        return
    cohort_track = await session.get(CohortTrack, cohort_assignment.cohort_track_id)
    if cohort_track is None:
        return
    enrollment = await session.scalar(
        select(CohortEnrollment)
        .join(CohortTrack, CohortTrack.track_version_id == CohortEnrollment.track_version_id)
        .where(
            CohortTrack.id == cohort_track.id,
            CohortEnrollment.student_user_id == student_assignment.student_user_id,
        )
    )
    if enrollment is None:
        return
    required_units = await session.scalar(
        select(func.count(InternshipUnit.id))
        .join(InternshipWeek, InternshipWeek.id == InternshipUnit.week_id)
        .join(InternshipPhase, InternshipPhase.id == InternshipWeek.phase_id)
        .where(
            InternshipPhase.cohort_track_id == cohort_track.id, InternshipUnit.is_required.is_(True)
        )
    )
    completed_units = await session.scalar(
        select(func.count(InternshipUnitCompletion.id)).where(
            InternshipUnitCompletion.enrollment_id == enrollment.id
        )
    )
    assignments = (
        await session.execute(
            select(InternshipStudentAssignment)
            .join(
                InternshipCohortAssignment,
                InternshipCohortAssignment.id == InternshipStudentAssignment.cohort_assignment_id,
            )
            .where(
                InternshipCohortAssignment.cohort_track_id == cohort_track.id,
                InternshipStudentAssignment.student_user_id == student_assignment.student_user_id,
            )
        )
    ).scalars()
    if (completed_units or 0) >= (required_units or 0) and all(
        item.final_result == "PASS" for item in assignments
    ):
        enrollment.certificate_eligibility = "ELIGIBLE"


async def finalize_review(
    session: AsyncSession,
    *,
    review_id: uuid.UUID,
    principal: SessionPrincipal,
    body: ReviewFinalizeRequest,
    correlation_id: uuid.UUID,
    idempotency_key: str | None = None,
) -> ReviewQueueItem:
    review = await session.scalar(
        select(InternshipReview).where(InternshipReview.id == review_id).with_for_update()
    )
    if review is None:
        raise NotFound("Review not found")
    if idempotency_key and review.idempotency_key == idempotency_key:
        rows = await review_queue(session, review_id=review.id, limit=1, offset=0)
        if not rows:
            raise NotFound("Review not found")
        return rows[0]
    if review.reviewer_id != principal.user_id:
        raise Forbidden("Review is not assigned to this reviewer")
    if review.status == "FINALIZED":
        raise InvalidState("Review is immutable after finalization")
    assignment = await session.get(InternshipStudentAssignment, review.student_assignment_id)
    submission = await session.get(InternshipSubmission, review.submission_id)
    cohort_assignment = await session.get(
        InternshipCohortAssignment, assignment.cohort_assignment_id if assignment else None
    )
    template = await session.get(
        InternshipAssignmentTemplate, cohort_assignment.template_id if cohort_assignment else None
    )
    if assignment is None or submission is None or template is None:
        raise NotFound("Review resources not found")
    if submission.version != body.version:
        raise Conflict("Submission version changed; reload the review")
    if body.conflict_declared:
        raise InvalidState("A conflicted reviewer cannot finalize a review")
    total = weighted_score(body.scores, template.rubric)
    review.status = "FINALIZED"
    review.scores = body.scores
    review.weighted_total = total
    review.student_feedback = body.student_feedback
    review.private_notes = body.private_notes
    review.conflict_declared = False
    review.decision = body.decision
    review.idempotency_key = idempotency_key
    review.finalized_at = now_utc()
    if body.decision == "PASS" and total < template.pass_score:
        raise ValidationFailure("PASS requires a score at or above the assignment threshold")
    assignment.final_result = body.decision if body.decision in {"PASS", "FAIL"} else None
    assignment.state = {
        "PASS": "PASSED",
        "CHANGES_REQUESTED": "CHANGES_REQUESTED",
        "FAIL": "FAILED",
    }[body.decision]
    await _refresh_certificate_eligibility(session, student_assignment=assignment)
    _audit(
        session,
        principal=principal,
        action="internship.review_finalized",
        resource_type="internship_review",
        resource_id=review.id,
        correlation_id=correlation_id,
        payload={"decision": body.decision, "weighted_total": total},
    )
    await session.commit()
    rows = await review_queue(session, review_id=review.id, limit=1, offset=0)
    if not rows:
        raise NotFound("Review not found after finalization")
    return rows[0]


async def issue_certificate(
    session: AsyncSession,
    *,
    enrollment_id: uuid.UUID,
    principal: SessionPrincipal,
    confirm: bool,
    idempotency_key: str,
    correlation_id: uuid.UUID,
) -> InternshipCertificate:
    if not confirm:
        raise ValidationFailure("Certificate issuance requires confirmation")
    enrollment = await session.get(CohortEnrollment, enrollment_id)
    if enrollment is None:
        raise NotFound("Enrollment not found")
    existing = await session.scalar(
        select(InternshipCertificate).where(InternshipCertificate.enrollment_id == enrollment.id)
    )
    if existing and existing.idempotency_key == idempotency_key:
        return existing
    if enrollment.certificate_eligibility != "APPROVED":
        raise InvalidState("Completion requires human approval before certificate issuance")
    if existing is not None:
        raise Conflict("Certificate already exists")
    student = await session.get(User, enrollment.student_user_id)
    track_version = await session.get(InternshipTrackVersion, enrollment.track_version_id)
    cohort = await session.get(InternshipCohort, enrollment.cohort_id)
    if student is None or track_version is None or cohort is None:
        raise NotFound("Certificate resources not found")
    certificate = InternshipCertificate(
        enrollment_id=enrollment.id,
        student_user_id=student.id,
        state="ISSUED",
        public_slug="internship-" + uuid.uuid4().hex,
        public_payload={
            "student_display_name": student.display_name,
            "program_name": "PraxisAI Internship",
            "cohort_name": cohort.name,
            "track_title": track_version.title,
            "evidence_source": "internship_learning",
            "is_demo": student.is_demo or cohort.is_demo,
        },
        issued_by_id=principal.user_id,
        issued_at=now_utc(),
        idempotency_key=idempotency_key,
    )
    enrollment.status = "COMPLETED"
    enrollment.completed_at = now_utc()
    session.add(certificate)
    _audit(
        session,
        principal=principal,
        action="internship.certificate_issued",
        resource_type="internship_certificate",
        resource_id=certificate.id,
        correlation_id=correlation_id,
    )
    await session.commit()
    return certificate


async def public_certificate(session: AsyncSession, *, public_slug: str) -> PublicCertificateView:
    certificate = await session.scalar(
        select(InternshipCertificate).where(InternshipCertificate.public_slug == public_slug)
    )
    if certificate is None or certificate.public_slug is None:
        raise NotFound("Certificate not found")
    return PublicCertificateView(
        state=certificate.state,
        public_slug=certificate.public_slug,
        payload=certificate.public_payload,
    )


def _upload_limits(artifact_type: str, filename: str) -> tuple[int, set[str]]:
    extension = filename.rsplit(".", 1)[-1].casefold() if "." in filename else ""
    if artifact_type == "zip":
        return 100 * 1024 * 1024, {"zip"}
    if artifact_type in {"pdf", "technical_report", "readme"}:
        return 25 * 1024 * 1024, {"pdf", "md", "txt"}
    if artifact_type in {"screenshot", "screenshots", "architecture_diagram"}:
        return 10 * 1024 * 1024, {"png", "jpg", "jpeg", "webp"}
    if artifact_type in {"notebook", "ipynb"}:
        return 20 * 1024 * 1024, {"ipynb", "json"}
    return 50 * 1024 * 1024, {extension} if extension else set()


async def initiate_upload(
    session: AsyncSession,
    *,
    principal: SessionPrincipal,
    body: UploadInitiateRequest,
    settings: Settings,
) -> UploadView:
    assignment = await get_assignment(
        session, principal=principal, assignment_id=body.assignment_id
    )
    if assignment.state in {"LOCKED", "PASSED", "FAILED", "WITHDRAWN"}:
        raise InvalidState("Assignment is not accepting uploads")
    safe_filename = body.filename.replace("\\", "/").rsplit("/", 1)[-1]
    if safe_filename in {"", ".", ".."} or safe_filename.count(".") > 1:
        raise ValidationFailure("Unsafe filename")
    if safe_filename.casefold().endswith((".html", ".htm", ".exe", ".dll", ".js", ".svg")):
        raise ValidationFailure("Executable or active content is not allowed")
    maximum, extensions = _upload_limits(body.artifact_type, safe_filename)
    extension = safe_filename.rsplit(".", 1)[-1].casefold() if "." in safe_filename else ""
    if body.size_bytes > maximum or not extension or extension not in extensions:
        raise ValidationFailure("Upload size or file extension is not allowed")
    upload_id = uuid.uuid4().hex
    storage_key = f"internships/{principal.user_id}/{upload_id}/{safe_filename}"
    upload = InternshipUpload(
        upload_id=upload_id,
        owner_user_id=principal.user_id,
        student_assignment_id=assignment.id,
        artifact_type=body.artifact_type,
        filename=safe_filename,
        content_type=body.content_type,
        size_bytes=body.size_bytes,
        sha256=body.sha256.casefold() if body.sha256 else None,
        storage_key=storage_key,
        state="INITIATED",
        expires_at=now_utc().replace(microsecond=0) + timedelta(hours=1),
    )
    session.add(upload)
    await session.commit()
    return UploadView(
        upload_id=upload.upload_id,
        artifact_type=upload.artifact_type,
        filename=upload.filename,
        state=upload.state,
        expires_at=upload.expires_at,
        upload_url=f"/api/v1/internships/uploads/{upload.upload_id}/content",
    )


async def receive_upload_content(
    session: AsyncSession,
    *,
    principal: SessionPrincipal,
    upload_id: str,
    content: bytes,
    settings: Settings,
) -> UploadView:
    async def chunks() -> AsyncIterator[bytes]:
        yield content

    return await receive_upload_stream(
        session,
        principal=principal,
        upload_id=upload_id,
        chunks=chunks(),
        settings=settings,
    )


async def receive_upload_stream(
    session: AsyncSession,
    *,
    principal: SessionPrincipal,
    upload_id: str,
    chunks: AsyncIterator[bytes],
    settings: Settings,
) -> UploadView:
    upload = await session.scalar(
        select(InternshipUpload).where(
            InternshipUpload.upload_id == upload_id,
            InternshipUpload.owner_user_id == principal.user_id,
        )
    )
    if upload is None:
        raise NotFound("Upload not found")
    if upload.state != "INITIATED" or now_utc() >= upload.expires_at:
        upload.state = "EXPIRED"
        await session.commit()
        raise InvalidState("Upload is expired or already completed")
    try:
        if settings.storage_provider == "supabase":
            digest, size = await SupabaseInternshipStorage(settings).put_stream(
                upload.storage_key, chunks, upload.content_type, upload.size_bytes
            )
        else:
            digest, size = await LocalInternshipStorage(
                settings.internship_local_storage_path
            ).put_stream(upload.storage_key, chunks)
    except SupabaseStorageError as exc:
        raise StorageFailure("Upload storage is temporarily unavailable") from exc
    if size != upload.size_bytes or (upload.sha256 and digest != upload.sha256):
        upload.state = "REJECTED"
        upload.scan_message = "Uploaded size or SHA-256 does not match initiation metadata"
        await session.commit()
        raise ValidationFailure(upload.scan_message)
    upload.sha256 = digest
    upload.state = "UPLOADED"
    await session.commit()
    return UploadView(
        upload_id=upload.upload_id,
        artifact_type=upload.artifact_type,
        filename=upload.filename,
        state=upload.state,
        expires_at=upload.expires_at,
        upload_url=f"/api/v1/internships/uploads/{upload.upload_id}/content",
    )


async def complete_upload(
    session: AsyncSession,
    *,
    principal: SessionPrincipal,
    upload_id: str,
    body: UploadCompleteRequest,
    settings: Settings,
) -> UploadView:
    upload = await session.scalar(
        select(InternshipUpload).where(
            InternshipUpload.upload_id == upload_id,
            InternshipUpload.owner_user_id == principal.user_id,
        )
    )
    if upload is None:
        raise NotFound("Upload not found")
    if upload.state != "UPLOADED":
        raise InvalidState("Upload is not ready for completion")
    if now_utc() >= upload.expires_at:
        upload.state = "EXPIRED"
        await session.commit()
        raise InvalidState("Upload is expired")
    if settings.app_env in {"staging", "production"}:
        if upload.sha256 != body.sha256.casefold():
            upload.state = "REJECTED"
            upload.scan_message = "SHA-256 mismatch"
            await session.commit()
            raise ValidationFailure("Upload hash does not match")
        upload.state = "QUARANTINED"
        upload.scan_message = (
            "Awaiting the production malware scanner; upload cannot be attached yet."
        )
        await session.commit()
        return UploadView(
            upload_id=upload.upload_id,
            artifact_type=upload.artifact_type,
            filename=upload.filename,
            state=upload.state,
            expires_at=upload.expires_at,
            upload_url=f"/api/v1/internships/uploads/{upload.upload_id}/content",
        )
    try:
        if settings.storage_provider == "supabase":
            content = await SupabaseInternshipStorage(settings).read(upload.storage_key)
        else:
            content = LocalInternshipStorage(settings.internship_local_storage_path).read(
                upload.storage_key
            )
    except (SupabaseStorageError, OSError) as exc:
        raise StorageFailure("Upload storage is temporarily unavailable") from exc
    actual_hash = hashlib.sha256(content).hexdigest()
    if actual_hash != body.sha256.casefold() or (upload.sha256 and actual_hash != upload.sha256):
        upload.state = "REJECTED"
        upload.scan_message = "SHA-256 mismatch"
        await session.commit()
        raise ValidationFailure("Upload hash does not match")
    scanner = (
        DemoScanner()
        if settings.app_env in {"local", "test", "demo"}
        else DisabledProductionScanner()
    )
    result = scanner.scan(
        content, declared_content_type=upload.content_type, filename=upload.filename
    )
    upload.sha256 = actual_hash
    upload.state = result.state
    upload.scan_message = result.message
    if result.state == "REJECTED":
        await session.commit()
        raise ValidationFailure(result.message)
    await session.commit()
    return UploadView(
        upload_id=upload.upload_id,
        artifact_type=upload.artifact_type,
        filename=upload.filename,
        state=upload.state,
        expires_at=upload.expires_at,
        upload_url=f"/api/v1/internships/uploads/{upload.upload_id}/content",
    )
