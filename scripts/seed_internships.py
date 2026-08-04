import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import (
    CohortEnrollment,
    CohortTrack,
    InternshipApplication,
    InternshipAssignmentTemplate,
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
    InternshipWeek,
    University,
    UniversityEmailDomain,
    User,
)

TRACKS = [
    (
        "ai-engineer",
        "AI Engineer",
        "Build grounded AI systems with explicit tools, evaluations, and human approval boundaries.",
        ["Python", "APIs", "Evaluation", "Responsible AI"],
    ),
    (
        "data-scientist",
        "Data Scientist",
        "Turn messy questions into reproducible analysis, statistical reasoning, and decision evidence.",
        ["Python", "Statistics", "Experiment design", "Communication"],
    ),
    (
        "machine-learning-engineer",
        "Machine Learning Engineer",
        "Design, validate, and ship maintainable machine-learning systems with operational safeguards.",
        ["Python", "Modeling", "MLOps", "Monitoring"],
    ),
    (
        "full-stack-web-developer",
        "Full-Stack Web Developer",
        "Deliver accessible web products from data boundary through tested interface and deployment.",
        ["TypeScript", "React", "APIs", "Accessibility"],
    ),
    (
        "data-analyst-bi",
        "Data Analyst and Business Intelligence",
        "Build trustworthy metrics, dashboards, and decision narratives from governed data.",
        ["SQL", "Metrics", "Dashboards", "Data quality"],
    ),
]


def _rubric() -> list[dict[str, object]]:
    return [
        {"id": "problem", "label": "Problem framing", "weight": 25, "max_score": 100},
        {"id": "implementation", "label": "Working implementation", "weight": 30, "max_score": 100},
        {"id": "evidence", "label": "Test and evidence quality", "weight": 25, "max_score": 100},
        {"id": "communication", "label": "Technical communication", "weight": 20, "max_score": 100},
    ]


async def seed_internship_demo(
    session: AsyncSession,
    *,
    users: dict[str, User],
    university: University,
) -> None:
    from seed_demo import identifier, upsert

    now = datetime.now(UTC).replace(microsecond=0)
    cohort_start = now - timedelta(days=14)
    program = await upsert(
        session,
        InternshipProgram,
        "internship-program-cohort-2",
        name="InventaCore Technology Internship — Cohort 2 (Demo data)",
        slug="inventacore-technology-internship",
        public_description=(
            "A four-week, evidence-based technology internship with structured learning, "
            "guided delivery, independent practice, and human review. Demo data."
        ),
        internal_description="Fictional demo program; not a real partner or employment promise.",
        status="ACTIVE",
        default_timezone="Asia/Karachi",
        duration_weeks=4,
        application_opens_at=cohort_start - timedelta(days=30),
        application_closes_at=now + timedelta(days=30),
        university_email_policy="APPROVED_OR_REVIEW",
        personal_email_exception_policy="REVIEW",
        is_demo=True,
    )
    cohort = await upsert(
        session,
        InternshipCohort,
        "internship-cohort-2",
        program_id=program.id,
        name="InventaCore Technology Internship — Cohort 2 (Demo data)",
        slug="cohort-2-demo",
        timezone="Asia/Karachi",
        starts_at=cohort_start,
        ends_at=cohort_start + timedelta(days=28),
        capacity=50,
        status="ACTIVE",
        application_deadline=now + timedelta(days=30),
        enrollment_deadline=now + timedelta(days=30),
        late_policy={"grace_period_minutes": 60},
        resubmission_policy={"maximum_attempts": 3},
        certificate_policy={"human_approval_required": True},
        coordinator_id=users["coordinator"].id,
        is_demo=True,
    )
    await upsert(
        session,
        UniversityEmailDomain,
        "internship-demo-university-domain",
        university_id=university.id,
        domain="student.demo",
        status="APPROVED",
        allow_subdomains=False,
        verification_method="demo_fixture",
        verified_at=now,
        verified_by_id=users["coordinator"].id,
    )

    ai_track_id: uuid.UUID | None = None
    ai_version_id: uuid.UUID | None = None
    ai_assignment_ids: list[uuid.UUID] = []
    for slug, name, summary, skills in TRACKS:
        track = await upsert(
            session,
            InternshipTrack,
            f"internship-track-{slug}",
            slug=slug,
            name=name,
            is_active=True,
            is_demo=True,
        )
        version = await upsert(
            session,
            InternshipTrackVersion,
            f"internship-track-version-{slug}-1",
            track_id=track.id,
            version=1,
            title=f"{name} — Cohort 2 curriculum (Demo data)",
            summary=summary,
            prerequisites=["Git and GitHub basics", "A reliable development environment"],
            skill_outcomes=skills,
            expected_weekly_hours=12,
            status="PUBLISHED",
            published_at=cohort_start - timedelta(days=21),
            published_by_id=users["coordinator"].id,
            is_demo=True,
        )
        if slug == "ai-engineer":
            ai_track_id = track.id
            ai_version_id = version.id
        cohort_track = await upsert(
            session,
            CohortTrack,
            f"internship-cohort-2-track-{slug}",
            cohort_id=cohort.id,
            track_version_id=version.id,
            capacity=10,
            reviewer_pool=[str(users["coordinator"].id)],
            instructor_id=users["coordinator"].id,
        )
        phase_types = ["LEARNING", "LEARNING", "PRACTICAL_PROJECT", "CAPSTONE"]
        phase_names = ["Foundations", "Track practice", "Guided project", "Independent capstone"]
        for week_number, (phase_type, phase_name) in enumerate(zip(phase_types, phase_names), 1):
            week_start = cohort_start + timedelta(days=(week_number - 1) * 7)
            phase = await upsert(
                session,
                InternshipPhase,
                f"internship-phase-{slug}-{week_number}",
                cohort_track_id=cohort_track.id,
                name=phase_name,
                phase_type=phase_type,
                ordinal=week_number,
                starts_at=week_start,
                ends_at=week_start + timedelta(days=7),
                completion_requirement={"required": True},
            )
            week = await upsert(
                session,
                InternshipWeek,
                f"internship-week-{slug}-{week_number}",
                phase_id=phase.id,
                week_number=week_number,
                title=f"Week {week_number}: {phase_name} (Demo data)",
                summary=f"A database-managed {phase_name.lower()} week for the {name} track.",
                starts_at=week_start,
                ends_at=week_start + timedelta(days=7),
                unlock_policy={"type": "DATE"},
                required_unit_count=2 if week_number < 3 else 0,
                required_assignment_count=1 if week_number >= 3 else 0,
            )
            if week_number < 3:
                unit_titles = [
                    f"{name}: foundations and workflow",
                    f"{name}: applied practice and evidence",
                ]
                for ordinal, title in enumerate(unit_titles, 1):
                    await upsert(
                        session,
                        InternshipUnit,
                        f"internship-unit-{slug}-{week_number}-{ordinal}",
                        week_id=week.id,
                        ordinal=ordinal,
                        unit_type="GUIDED_LAB" if ordinal == 2 else "ARTICLE",
                        title=f"{title} (Demo data)",
                        summary="Original demo summary with an observable practice outcome.",
                        objectives=[f"Explain one {name} workflow decision", "Produce reviewable evidence"],
                        resources=[
                            {
                                "title": "Official reference",
                                "resource_type": "DOCUMENTATION",
                                "url": "https://docs.python.org/3/",
                                "duration_minutes": 25,
                                "accessibility_notes": "Text-first reference",
                            }
                        ],
                        practical_exercise="Create a small, tested artifact and write a short reflection.",
                        completion_rule={"evidence_summary": True, "minimum_length": 20},
                        prerequisites=[],
                        release_at=week_start,
                        deadline=week_start + timedelta(days=7),
                        is_required=True,
                        version=1,
                        is_demo=True,
                    )
            else:
                title = (
                    "Build a support-request classification and routing assistant"
                    if week_number == 3 and slug == "ai-engineer"
                    else f"{name}: {'guided delivery' if week_number == 3 else 'capstone delivery'}"
                )
                template = await upsert(
                    session,
                    InternshipAssignmentTemplate,
                    f"internship-assignment-template-{slug}-{week_number}",
                    track_version_id=version.id,
                    week_id=week.id,
                    title=f"{title} (Demo data)",
                    summary="A bounded internship project with explicit acceptance evidence.",
                    problem_statement="Translate a realistic user need into a safe, tested, explainable delivery.",
                    objectives=["Frame the problem", "Implement a working solution", "Document trade-offs"],
                    required_skills=skills,
                    estimated_effort_hours=18 if week_number == 3 else 28,
                    starter_resources=[{"title": "Project brief", "resource_type": "REFERENCE"}],
                    constraints=["Do not use private data", "Document limitations and safety boundaries"],
                    deliverables=["Working implementation", "README", "Technical reflection"],
                    acceptance_criteria=["The happy path works", "Tests are reproducible", "Known limitations are explicit"],
                    required_artifact_types=(
                        [
                            {"type": "github_url", "required": True},
                            {"type": "readme", "required": True},
                            {"type": "architecture_diagram", "required": True},
                            {"type": "screenshots", "required": True},
                            {"type": "test_report", "required": True},
                            {"type": "reflection", "required": True},
                        ]
                        if week_number == 3
                        else [
                            {"type": "github_url", "required": True},
                            {"type": "technical_report", "required": True},
                            {"type": "architecture_diagram", "required": True},
                            {"type": "evaluation_plan", "required": True},
                            {"type": "reflection", "required": True},
                        ]
                    ),
                    rubric=_rubric(),
                    maximum_score=100,
                    pass_score=70,
                    late_policy={"grace_period_minutes": 60},
                    resubmission_policy={"maximum_attempts": 3},
                    version=1,
                    is_demo=True,
                )
                cohort_assignment = await upsert(
                    session,
                    InternshipCohortAssignment,
                    f"internship-cohort-assignment-{slug}-{week_number}",
                    template_id=template.id,
                    cohort_track_id=cohort_track.id,
                    release_at=now - timedelta(hours=1) if week_number == 3 else now + timedelta(days=7),
                    deadline=week_start + timedelta(days=7),
                    grace_period_minutes=60,
                    review_deadline=week_start + timedelta(days=10),
                    status="PUBLISHED",
                    reviewer_pool=[str(users["coordinator"].id)],
                    publish_idempotency_key=f"demo-publish-{slug}-{week_number}",
                )
                if slug == "ai-engineer":
                    ai_assignment_ids.append(cohort_assignment.id)

    if ai_track_id is None or ai_version_id is None or len(ai_assignment_ids) != 2:
        raise RuntimeError("AI Engineer demo track was not seeded")
    enrollment = await upsert(
        session,
        CohortEnrollment,
        "internship-enrollment-amina-cohort-2",
        cohort_id=cohort.id,
        student_user_id=users["student"].id,
        track_version_id=ai_version_id,
        status="LEARNING",
        started_at=cohort_start,
        progress_snapshot={"week_1": "COMPLETE", "week_2": "IN_PROGRESS"},
        certificate_eligibility="NOT_ELIGIBLE",
        version=1,
    )
    application = await upsert(
        session,
        InternshipApplication,
        "internship-application-amina-cohort-2",
        applicant_user_id=users["student"].id,
        program_id=program.id,
        cohort_id=cohort.id,
        primary_track_id=ai_track_id,
        education_status="Undergraduate",
        university_id=university.id,
        degree_program="Computer Science",
        semester_status="Final year",
        country="PK",
        timezone="Asia/Karachi",
        weekly_availability_hours=12,
        technical_background="Python, APIs, and frontend foundations. Demo data.",
        motivation="Build evidence through a supervised technology internship. Demo data.",
        github_url="https://github.com/example/demo-student",
        email_verification_evidence={"verified": True, "domain": "student.demo", "demo": True},
        consent_snapshot={"terms_version": "demo-1", "demo": True},
        status="ACCEPTED",
        version=3,
        submitted_at=cohort_start - timedelta(days=5),
        decision_at=cohort_start - timedelta(days=3),
        decision_reason="Accepted for the AI Engineer track. Demo data.",
        reviewer_id=users["coordinator"].id,
        correlation_id=identifier("internship-application-correlation-amina"),
        submit_idempotency_key="demo-application-submit-amina",
    )
    del application
    for week_number in (1,):
        units = (
            await session.execute(
                select(InternshipUnit)
                .join(InternshipWeek, InternshipWeek.id == InternshipUnit.week_id)
                .join(InternshipPhase, InternshipPhase.id == InternshipWeek.phase_id)
                .join(CohortTrack, CohortTrack.id == InternshipPhase.cohort_track_id)
                .where(CohortTrack.track_version_id == ai_version_id, InternshipWeek.week_number == week_number)
            )
        ).scalars()
        for unit in units:
            await upsert(
                session,
                InternshipUnitCompletion,
                f"internship-completion-amina-{unit.id}",
                enrollment_id=enrollment.id,
                unit_id=unit.id,
                evidence={"summary": "Completed and reflected on the demo exercise."},
                completed_at=cohort_start + timedelta(days=6),
            )
    current_assignment = await upsert(
        session,
        InternshipStudentAssignment,
        "internship-student-assignment-amina-project-1",
        cohort_assignment_id=ai_assignment_ids[0],
        student_user_id=users["student"].id,
        state="IN_PROGRESS",
        started_at=now - timedelta(days=1),
        due_at=now + timedelta(days=6),
        attempt_count=1,
        version=2,
    )
    locked_assignment = await upsert(
        session,
        InternshipStudentAssignment,
        "internship-student-assignment-amina-project-2",
        cohort_assignment_id=ai_assignment_ids[1],
        student_user_id=users["student"].id,
        state="LOCKED",
        due_at=now + timedelta(days=13),
        attempt_count=0,
        version=1,
    )
    del locked_assignment
    reviewed_submission = await upsert(
        session,
        InternshipSubmission,
        "internship-reviewed-submission-amina-project-1",
        student_assignment_id=current_assignment.id,
        student_user_id=users["student"].id,
        state="FINALIZED",
        version=1,
        links={"github_url": "https://github.com/example/demo-routing-assistant"},
        text_fields={"readme": "Demo README", "reflection": "Demo reflection", "test_report": "Demo tests", "architecture_diagram": "Demo architecture", "screenshots": "Demo screenshots"},
        artifact_upload_ids=[],
        canonical_hash="d" * 64,
        rubric_version=1,
        submitted_at=now - timedelta(days=1),
        deadline_status="ON_TIME",
        correlation_id=identifier("internship-reviewed-submission-correlation"),
    )
    draft = await upsert(
        session,
        InternshipSubmission,
        "internship-draft-submission-amina-project-1",
        student_assignment_id=current_assignment.id,
        student_user_id=users["student"].id,
        state="DRAFT",
        version=2,
        links={},
        text_fields={"reflection": "Draft in progress. Demo data."},
        artifact_upload_ids=[],
        previous_submission_id=reviewed_submission.id,
        correlation_id=identifier("internship-draft-submission-correlation"),
    )
    current_assignment.current_submission_id = draft.id
    await upsert(
        session,
        InternshipReview,
        "internship-review-amina-project-1",
        student_assignment_id=current_assignment.id,
        submission_id=reviewed_submission.id,
        reviewer_id=users["coordinator"].id,
        status="FINALIZED",
        scores=[
            {"criterion_id": "problem", "score": 85},
            {"criterion_id": "implementation", "score": 80},
            {"criterion_id": "evidence", "score": 88},
            {"criterion_id": "communication", "score": 82},
        ],
        weighted_total=83,
        student_feedback="The demo routing assistant has a clear boundary and useful test evidence. Demo data.",
        private_notes="Sample review for the demo walkthrough; not a live employment evaluation.",
        decision="PASS",
        finalized_at=now - timedelta(hours=12),
        idempotency_key="demo-review-amina-project-1",
    )
