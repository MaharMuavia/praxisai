import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.auth.service import SessionPrincipal
from app.domain.models import Base, LearningModule, LearningPath, StudentProfile, User
from app.domain.schemas import LearningModuleCompleteRequest
from app.learning.service import LearningError, complete_module, enroll_in_path, list_learning_paths


@pytest.mark.asyncio
async def test_student_completes_a_learning_path_in_sequence_with_evidence() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    student_id = uuid.uuid4()
    organization_id = uuid.uuid4()
    principal = SessionPrincipal(student_id, organization_id, "student")
    async with factory() as session:
        session: AsyncSession
        session.add(
            User(
                id=student_id,
                email="student@example.test",
                display_name="Test Student",
                external_subject="test-student",
            )
        )
        session.add(
            StudentProfile(
                user_id=student_id,
                confirmed_18_plus=True,
                eligible=True,
            )
        )
        path = LearningPath(
            slug="accessible-frontend-delivery",
            title="Accessible frontend delivery",
            summary="Practice translating a real brief into a tested accessible interface.",
            level="FOUNDATION",
            estimated_hours=6,
            skill_outcomes=["Requirements analysis", "Accessible implementation"],
            prerequisites=[],
        )
        session.add(path)
        await session.flush()
        first = LearningModule(
            learning_path_id=path.id,
            ordinal=1,
            title="Read the brief",
            summary="Extract users, outcomes, constraints, and acceptance criteria.",
            estimated_minutes=45,
            content_sections=[
                {"title": "Business context", "body": "Identify the user and outcome."}
            ],
            exercise_brief="Write acceptance criteria for an accessible service form.",
            completion_evidence="A concise criteria summary.",
        )
        second = LearningModule(
            learning_path_id=path.id,
            ordinal=2,
            title="Build and verify",
            summary="Implement the interface and collect meaningful verification evidence.",
            estimated_minutes=90,
            content_sections=[{"title": "Verification", "body": "Test behavior, not visibility."}],
            exercise_brief="Implement and test the form flow.",
            completion_evidence="A test summary and artifact reference.",
        )
        session.add_all([first, second])
        await session.commit()

        initial = await list_learning_paths(session, principal=principal)
        assert initial[0].progress_percent == 0
        assert initial[0].enrolled is False

        enrolled = await enroll_in_path(
            session,
            path_id=path.id,
            principal=principal,
            correlation_id=uuid.uuid4(),
        )
        assert enrolled.enrolled is True

        with pytest.raises(LearningError, match="previous module"):
            await complete_module(
                session,
                module_id=second.id,
                body=LearningModuleCompleteRequest(
                    evidence_summary="Implemented the flow and recorded keyboard test evidence."
                ),
                principal=principal,
                correlation_id=uuid.uuid4(),
            )

        halfway = await complete_module(
            session,
            module_id=first.id,
            body=LearningModuleCompleteRequest(
                evidence_summary=(
                    "Documented users, constraints, and five testable acceptance criteria."
                )
            ),
            principal=principal,
            correlation_id=uuid.uuid4(),
        )
        assert halfway.progress_percent == 50

        completed = await complete_module(
            session,
            module_id=second.id,
            body=LearningModuleCompleteRequest(
                evidence_summary=(
                    "Implemented the form and captured automated and keyboard verification results."
                )
            ),
            principal=principal,
            correlation_id=uuid.uuid4(),
        )
        assert completed.progress_percent == 100
        assert completed.status == "COMPLETED"

    await engine.dispose()


@pytest.mark.asyncio
async def test_ineligible_student_cannot_enroll() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    student_id = uuid.uuid4()
    async with factory() as session:
        session.add(
            User(
                id=student_id,
                email="minor@example.test",
                display_name="Ineligible Student",
                external_subject="ineligible-student",
            )
        )
        session.add(StudentProfile(user_id=student_id, confirmed_18_plus=False, eligible=True))
        path = LearningPath(
            slug="restricted-path",
            title="Restricted path",
            summary="A path that still applies platform eligibility policy.",
            level="FOUNDATION",
            estimated_hours=2,
            skill_outcomes=["Policy awareness"],
            prerequisites=[],
        )
        session.add(path)
        await session.commit()

        with pytest.raises(LearningError, match="age-confirmed"):
            await enroll_in_path(
                session,
                path_id=path.id,
                principal=SessionPrincipal(student_id, uuid.uuid4(), "student"),
                correlation_id=uuid.uuid4(),
            )

    await engine.dispose()
