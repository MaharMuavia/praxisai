import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.auth.service import SessionPrincipal
from app.config import Settings
from app.domain.models import (
    AuditEvent,
    Base,
    ExportJob,
    InstitutionalAgreement,
    Organization,
    OutboxEvent,
    StudentProfile,
    University,
    UniversityEnrollment,
    User,
)
from app.university.service import UniversityConflict, aggregate_metrics, request_export


@pytest.mark.asyncio
async def test_university_metrics_are_suppressed_below_consented_cohort() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    async with factory() as session:
        organization = Organization(
            name="Fictional University",
            slug="university-reporting",
            kind="university",
            is_demo=True,
        )
        viewer = User(email="viewer@example.test", display_name="Viewer")
        session.add_all([organization, viewer])
        await session.flush()
        university = University(organization_id=organization.id, agreement_status="ACTIVE")
        session.add(university)
        await session.flush()
        session.add(
            InstitutionalAgreement(
                university_id=university.id,
                version=1,
                status="ACTIVE",
                entitlements=["aggregate_metrics", "exports"],
                starts_at=datetime.now(UTC) - timedelta(days=1),
                ends_at=datetime.now(UTC) + timedelta(days=30),
            )
        )
        enrollments: list[UniversityEnrollment] = []
        for index in range(5):
            student = User(email=f"student-{index}@example.test", display_name=f"Student {index}")
            session.add(student)
            await session.flush()
            profile = StudentProfile(
                user_id=student.id,
                bio="Test profile",
                confirmed_18_plus=True,
            )
            session.add(profile)
            await session.flush()
            enrollment = UniversityEnrollment(
                university_id=university.id,
                student_profile_id=profile.id,
                consented=True,
            )
            enrollments.append(enrollment)
            session.add(enrollment)
        await session.commit()

        principal = SessionPrincipal(
            user_id=viewer.id,
            organization_id=organization.id,
            role="university_viewer",
        )
        settings = Settings(
            app_env="test",
            demo_mode=True,
            university_minimum_cohort_size=5,
        )
        visible = await aggregate_metrics(session, principal=principal, settings=settings)
        assert visible.suppressed is False
        assert visible.consented_cohort_size == 5
        assert visible.participating_students == 0

        enrollments[0].consented = False
        await session.commit()
        suppressed = await aggregate_metrics(session, principal=principal, settings=settings)
        assert suppressed.suppressed is True
        assert suppressed.consented_cohort_size is None
        assert suppressed.verified_work_minutes is None

        with pytest.raises(UniversityConflict):
            await request_export(
                session,
                principal=principal,
                purpose="Evaluate aggregate outcomes for the approved academic program.",
                idempotency_key="suppressed-export",
                correlation_id=uuid.uuid4(),
                settings=settings,
            )
        enrollments[0].consented = True
        await session.commit()

        export = await request_export(
            session,
            principal=principal,
            purpose="Evaluate aggregate outcomes for the approved academic program.",
            idempotency_key="university-export-once",
            correlation_id=uuid.uuid4(),
            settings=settings,
        )
        repeated = await request_export(
            session,
            principal=principal,
            purpose="Evaluate aggregate outcomes for the approved academic program.",
            idempotency_key="university-export-once",
            correlation_id=uuid.uuid4(),
            settings=settings,
        )
        assert export.id == repeated.id
        assert await session.scalar(select(func.count(ExportJob.id))) == 1
        assert await session.scalar(select(func.count(OutboxEvent.id))) == 1
        assert await session.scalar(select(func.count(AuditEvent.id))) == 1

        from app.university.service import get_export_csv_content

        job, csv_data = await get_export_csv_content(
            session, export_id=export.id, principal=principal, settings=settings
        )
        assert job.id == export.id
        assert "Perkins V (WBL)" in csv_data
        assert "IPEDS" in csv_data
        assert "Full-Stack Web & Cloud Systems" in csv_data
    await engine.dispose()
