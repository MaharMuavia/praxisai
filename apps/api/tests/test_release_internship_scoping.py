import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.auth.service import SessionPrincipal
from app.domain.models import (
    Base,
    CohortEnrollment,
    CohortTrack,
    InternshipApplication,
    InternshipCohort,
    InternshipProgram,
    InternshipSubmission,
    InternshipTrack,
    InternshipTrackVersion,
    User,
)
from app.internships.enrollments.context import resolve_enrollment_context
from app.internships.schemas import ApplicationUpdate, SubmissionUpdateRequest
from app.internships.service import (
    Conflict,
    NotFound,
    certificate_eligibility_for_enrollment,
    decide_completion,
    get_application,
    save_submission,
    submit_application,
    update_application,
)


@pytest.fixture
async def session() -> AsyncSession:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    async with factory() as value:
        yield value
    await engine.dispose()


async def _student_and_program(session: AsyncSession) -> tuple[User, InternshipProgram]:
    student = User(email="student@example.test", display_name="Student", is_demo=True)
    program = InternshipProgram(
        slug="program-" + uuid.uuid4().hex,
        name="Program",
        public_description="A test program",
        duration_weeks=4,
        status="APPLICATIONS_OPEN",
        is_demo=True,
    )
    session.add_all([student, program])
    await session.flush()
    return student, program


def _principal(student: User) -> SessionPrincipal:
    return SessionPrincipal(student.id, uuid.uuid4(), "student")


@pytest.mark.asyncio
async def test_application_updates_target_id_when_student_has_two_cohorts(
    session: AsyncSession,
) -> None:
    student, program = await _student_and_program(session)
    first, second = uuid.uuid4(), uuid.uuid4()
    first_application = InternshipApplication(
        id=first,
        applicant_user_id=student.id,
        program_id=program.id,
        cohort_id=uuid.uuid4(),
        correlation_id=uuid.uuid4(),
    )
    second_application = InternshipApplication(
        id=second,
        applicant_user_id=student.id,
        program_id=program.id,
        cohort_id=uuid.uuid4(),
        correlation_id=uuid.uuid4(),
    )
    session.add_all([first_application, second_application])
    await session.commit()

    updated = await update_application(
        session,
        principal=_principal(student),
        application_id=first,
        body=ApplicationUpdate(expected_version=1, motivation="first cohort application"),
        correlation_id=uuid.uuid4(),
    )

    assert updated.id == first
    assert updated.motivation == "first cohort application"
    untouched = await session.get(InternshipApplication, second)
    assert untouched is not None
    assert untouched.motivation == ""


@pytest.mark.asyncio
async def test_application_id_is_owned_by_the_authenticated_student(session: AsyncSession) -> None:
    student, program = await _student_and_program(session)
    other = User(email="other@example.test", display_name="Other", is_demo=True)
    session.add(other)
    await session.flush()
    application = InternshipApplication(
        applicant_user_id=other.id,
        program_id=program.id,
        cohort_id=uuid.uuid4(),
        correlation_id=uuid.uuid4(),
    )
    session.add(application)
    await session.commit()

    with pytest.raises(NotFound):
        await get_application(
            session,
            principal=_principal(student),
            application_id=application.id,
        )


@pytest.mark.asyncio
async def test_submit_is_idempotent_and_stale_updates_are_rejected(session: AsyncSession) -> None:
    student, program = await _student_and_program(session)
    application = InternshipApplication(
        applicant_user_id=student.id,
        program_id=program.id,
        cohort_id=uuid.uuid4(),
        primary_track_id=uuid.uuid4(),
        education_status="Undergraduate",
        degree_program="Computer Science",
        country="PK",
        timezone="Asia/Karachi",
        weekly_availability_hours=12,
        technical_background="Python and SQL",
        motivation="I want to learn through evidence.",
        correlation_id=uuid.uuid4(),
    )
    session.add(application)
    await session.commit()
    principal = _principal(student)

    submitted = await submit_application(
        session,
        principal=principal,
        application_id=application.id,
        expected_version=1,
        consent_version="v1",
        idempotency_key="application-submit-1",
        correlation_id=uuid.uuid4(),
    )
    replay = await submit_application(
        session,
        principal=principal,
        application_id=application.id,
        expected_version=1,
        consent_version="v1",
        idempotency_key="application-submit-1",
        correlation_id=uuid.uuid4(),
    )
    assert submitted.status == replay.status == "SUBMITTED"
    assert submitted.version == replay.version == 2
    with pytest.raises(Conflict):
        await update_application(
            session,
            principal=principal,
            application_id=application.id,
            body=ApplicationUpdate(expected_version=1, motivation="stale edit"),
            correlation_id=uuid.uuid4(),
        )


@pytest.mark.asyncio
async def test_enrollment_context_requires_selection_and_keeps_cohorts_separate(
    session: AsyncSession,
) -> None:
    student, program = await _student_and_program(session)
    track = InternshipTrack(slug="track-" + uuid.uuid4().hex, name="Track")
    session.add(track)
    await session.flush()
    version = InternshipTrackVersion(
        track_id=track.id,
        version=1,
        title="Track v1",
        summary="Summary",
        status="PUBLISHED",
    )
    now = datetime.now(UTC)
    cohort_a = InternshipCohort(
        program_id=program.id,
        name="Cohort A",
        slug="a-" + uuid.uuid4().hex,
        starts_at=now,
        ends_at=now + timedelta(days=30),
        capacity=10,
        status="ACTIVE",
    )
    cohort_b = InternshipCohort(
        program_id=program.id,
        name="Cohort B",
        slug="b-" + uuid.uuid4().hex,
        starts_at=now,
        ends_at=now + timedelta(days=30),
        capacity=10,
        status="ACTIVE",
    )
    session.add_all([version, cohort_a, cohort_b])
    await session.flush()
    track_a = CohortTrack(cohort_id=cohort_a.id, track_version_id=version.id, capacity=10)
    track_b = CohortTrack(cohort_id=cohort_b.id, track_version_id=version.id, capacity=10)
    enrollment_a = CohortEnrollment(
        cohort_id=cohort_a.id, student_user_id=student.id, track_version_id=version.id
    )
    enrollment_b = CohortEnrollment(
        cohort_id=cohort_b.id, student_user_id=student.id, track_version_id=version.id
    )
    session.add_all([track_a, track_b, enrollment_a, enrollment_b])
    await session.commit()
    principal = _principal(student)

    with pytest.raises(ValueError, match="explicit enrollment"):
        await resolve_enrollment_context(session, principal=principal)
    context = await resolve_enrollment_context(
        session, principal=principal, enrollment_id=enrollment_b.id
    )
    assert context.enrollment_id == enrollment_b.id
    assert context.cohort_id == cohort_b.id
    assert context.cohort_track_id == track_b.id


@pytest.mark.asyncio
async def test_completion_decision_returns_target_eligibility_and_replays_by_key(
    session: AsyncSession,
) -> None:
    student, program = await _student_and_program(session)
    now = datetime.now(UTC)
    cohort = InternshipCohort(
        program_id=program.id,
        name="Cohort",
        slug="completion-" + uuid.uuid4().hex,
        starts_at=now,
        ends_at=now + timedelta(days=30),
        capacity=10,
        status="ACTIVE",
    )
    track = InternshipTrack(slug="completion-track-" + uuid.uuid4().hex, name="Track")
    session.add(track)
    await session.flush()
    version = InternshipTrackVersion(
        track_id=track.id,
        version=1,
        title="Track",
        summary="Summary",
        status="PUBLISHED",
    )
    session.add_all([cohort, version])
    await session.flush()
    session.add(CohortTrack(cohort_id=cohort.id, track_version_id=version.id, capacity=10))
    enrollment = CohortEnrollment(
        cohort_id=cohort.id,
        student_user_id=student.id,
        track_version_id=version.id,
        certificate_eligibility="ELIGIBLE",
        version=4,
    )
    session.add(enrollment)
    await session.commit()

    coordinator = SessionPrincipal(uuid.uuid4(), uuid.uuid4(), "coordinator")
    result = await decide_completion(
        session,
        enrollment_id=enrollment.id,
        principal=coordinator,
        decision="APPROVED",
        reason="All required evidence passed human review.",
        expected_version=4,
        idempotency_key="completion-decision-1",
        correlation_id=uuid.uuid4(),
    )
    replay = await decide_completion(
        session,
        enrollment_id=enrollment.id,
        principal=coordinator,
        decision="APPROVED",
        reason="All required evidence passed human review.",
        expected_version=4,
        idempotency_key="completion-decision-1",
        correlation_id=uuid.uuid4(),
    )
    assert result.enrollment_id == enrollment.id
    assert result.state == replay.state == "APPROVED"
    assert (
        await certificate_eligibility_for_enrollment(session, enrollment.id)
    ).enrollment_id == enrollment.id


@pytest.mark.asyncio
async def test_submission_draft_save_increments_version_and_rejects_stale_save(
    session: AsyncSession,
) -> None:
    student = User(email="submitter@example.test", display_name="Submitter", is_demo=True)
    session.add(student)
    await session.flush()
    submission = InternshipSubmission(
        student_assignment_id=uuid.uuid4(),
        student_user_id=student.id,
        correlation_id=uuid.uuid4(),
        version=1,
    )
    session.add(submission)
    await session.commit()
    principal = _principal(student)

    saved = await save_submission(
        session,
        principal=principal,
        submission_id=submission.id,
        body=SubmissionUpdateRequest(expected_version=1, text_fields={"summary": "saved"}),
    )
    assert saved.version == 2
    with pytest.raises(Conflict):
        await save_submission(
            session,
            principal=principal,
            submission_id=submission.id,
            body=SubmissionUpdateRequest(expected_version=1, text_fields={"summary": "stale"}),
        )
