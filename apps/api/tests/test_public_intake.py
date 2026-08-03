import uuid
from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient
from pydantic import TypeAdapter, ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.auth.service import SessionCodec, SessionPrincipal
from app.config import get_settings
from app.db import get_session
from app.domain.models import (
    AuditEvent,
    Base,
    Organization,
    OrganizationMembership,
    PublicIntakeSubmission,
    User,
)
from app.domain.schemas import PublicIntakeSubmissionCreate
from app.main import app


def test_public_intake_contract_requires_true_consent_and_expert_evidence() -> None:
    adapter = TypeAdapter(PublicIntakeSubmissionCreate)
    expert = {
        "kind": "expert_lead",
        "full_name": "Expert Example",
        "email": "expert@example.org",
        "country": "Pakistan",
        "consent": True,
        "technical_specializations": "Python and data systems",
        "years_experience": 8,
        "weekly_availability": 10,
        "experience_summary": "I have delivered production data systems for multiple teams.",
        "profile_url": "https://example.org/expert",
    }
    parsed = adapter.validate_python(expert)
    assert parsed.years_experience == 8
    assert parsed.experience_summary.startswith("I have delivered")
    with pytest.raises(ValidationError):
        adapter.validate_python({**expert, "consent": False})
    with pytest.raises(ValidationError):
        adapter.validate_python({key: value for key, value in expert.items() if key != "consent"})


@pytest.mark.asyncio
async def test_public_company_intake_is_persisted_and_idempotent() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    async def override_session() -> AsyncIterator[AsyncSession]:
        async with factory() as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    payload = {
        "kind": "company",
        "full_name": "Taylor Example",
        "email": "taylor@example.org",
        "country": "Pakistan",
        "consent": True,
        "company_name": "Example Studio",
        "business_problem": "We need a reviewed workflow for a recurring internal process.",
        "desired_result": "A tested and documented review surface for the operations team.",
        "project_category": "workflow_automation",
        "target_timeline": "This quarter",
        "data_sensitivity": "internal",
        "honeypot": "",
    }
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            first = await client.post(
                "/api/v1/public/company",
                headers={"Idempotency-Key": "company-intake-001"},
                json=payload,
            )
            second = await client.post(
                "/api/v1/public/company",
                headers={"Idempotency-Key": "company-intake-001"},
                json=payload,
            )

        assert first.status_code == 201, first.text
        assert second.status_code == 201
        assert first.json()["id"] == second.json()["id"]
        async with factory() as session:
            submissions = list((await session.scalars(select(PublicIntakeSubmission))).all())
            audits = list((await session.scalars(select(AuditEvent))).all())
            assert len(submissions) == 1
            assert len(audits) == 1
            assert submissions[0].payload["full_name"] == "Taylor Example"
            assert "email" not in submissions[0].payload
    finally:
        app.dependency_overrides.clear()
        await engine.dispose()


@pytest.mark.asyncio
async def test_operations_can_review_public_intake() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    org = Organization(name="Operations", slug="operations", kind="internal")
    user = User(email="ops@example.test", display_name="Ops", is_demo=True)
    async with factory() as session:
        session.add_all([org, user])
        await session.flush()
        session.add(
            OrganizationMembership(user_id=user.id, organization_id=org.id, role="coordinator")
        )
        await session.commit()

    async def override_session() -> AsyncIterator[AsyncSession]:
        async with factory() as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    try:
        async with factory() as session:
            submission = PublicIntakeSubmission(
                kind="student",
                status="NEW",
                contact_email="student@example.test",
                payload={"full_name": "Student"},
                consent_snapshot={"granted": True},
                idempotency_key="student-intake-001",
                correlation_id=uuid.uuid4(),
            )
            session.add(submission)
            await session.commit()
            submission_id = submission.id
        token = SessionCodec(get_settings().session_secret).encode(
            SessionPrincipal(user.id, org.id, "coordinator")
        )
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            client.cookies.set("praxis_session", token)
            client.cookies.set("praxis_csrf", "csrf")
            response = await client.patch(
                f"/api/v1/ops/intake/{submission_id}",
                headers={"X-CSRF-Token": "csrf"},
                json={
                    "status": "IN_REVIEW",
                    "qualification_notes": "Needs a human follow-up.",
                    "expected_version": 1,
                },
            )
        assert response.status_code == 200
        assert response.json()["status"] == "IN_REVIEW"
    finally:
        app.dependency_overrides.clear()
        await engine.dispose()
