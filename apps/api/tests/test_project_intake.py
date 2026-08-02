import uuid
from datetime import date

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from starlette.requests import Request

from app.api.projects import run_planning_agent, run_scope_agent
from app.auth.service import SessionPrincipal
from app.config import Settings
from app.domain.enums import ProjectState
from app.domain.models import (
    AcceptanceCriterion,
    AgentRun,
    AuditEvent,
    Base,
    PlanRun,
    Project,
    ProjectScopeVersion,
)
from app.projects.service import project_intake_snapshot


@pytest.mark.asyncio
async def test_scoping_reuses_the_immutable_client_intake_snapshot() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    creator_id = uuid.uuid4()
    organization_id = uuid.uuid4()
    async with factory() as session:
        session: AsyncSession
        project = Project(
            client_organization_id=organization_id,
            created_by_id=creator_id,
            title="Accessible student services portal",
            description="Build a constrained portal for student support requests and reporting.",
            category="authenticated_crud",
        )
        session.add(project)
        await session.flush()
        session.add(
            AuditEvent(
                actor_id=creator_id,
                organization_id=organization_id,
                action="project.created",
                resource_type="project",
                resource_id=project.id,
                correlation_id=uuid.uuid4(),
                payload={
                    "submitted_snapshot": {
                        "title": project.title,
                        "description": project.description,
                        "category": project.category,
                        "desired_outcome": "Reduce support request turnaround time",
                        "target_users": "University students and support coordinators",
                        "deliverables": ["Authenticated request workflow", "Reporting dashboard"],
                        "constraints": ["WCAG AA", "No sensitive health data"],
                        "desired_deadline": "2026-08-14",
                        "budget_guidance_minor": 250000,
                        "data_sensitivity": "confidential",
                        "attachment_references": ["https://example.test/brief.pdf"],
                    }
                },
            )
        )
        await session.commit()

        snapshot = await project_intake_snapshot(session, project)

    assert snapshot.desired_outcome == "Reduce support request turnaround time"
    assert snapshot.deliverables == ["Authenticated request workflow", "Reporting dashboard"]
    assert snapshot.desired_deadline == date(2026, 8, 14)
    assert snapshot.data_sensitivity == "confidential"
    await engine.dispose()


@pytest.mark.asyncio
async def test_planning_reuses_a_current_proposal_for_the_accepted_scope() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    coordinator_id = uuid.uuid4()
    organization_id = uuid.uuid4()
    async with factory() as session:
        project = Project(
            client_organization_id=organization_id,
            created_by_id=coordinator_id,
            title="Retry-safe project plan",
            description="Generate one criteria-bound plan even when operations retry.",
            category="website",
            state=ProjectState.READY_TO_START.value,
            funded_minor=10_000,
            required_deposit_minor=10_000,
        )
        session.add(project)
        await session.flush()
        scope = ProjectScopeVersion(
            project_id=project.id,
            version=1,
            status="CLIENT_ACCEPTED",
            snapshot={},
        )
        session.add(scope)
        await session.flush()
        session.add(
            AcceptanceCriterion(
                scope_version_id=scope.id,
                ordinal=1,
                description="The approved workflow has durable test evidence.",
            )
        )
        await session.commit()
        principal = SessionPrincipal(coordinator_id, organization_id, "coordinator")
        request = Request({"type": "http", "client": ("127.0.0.1", 12345)})
        settings = Settings(
            app_env="test",
            demo_mode=True,
            gemini_provider="fixture",
            database_url="sqlite+aiosqlite:///:memory:",
        )

        first = await run_planning_agent(
            project.id,
            request,
            principal,
            session,
            settings,
            uuid.uuid4(),
        )
        second = await run_planning_agent(
            project.id,
            request,
            principal,
            session,
            settings,
            uuid.uuid4(),
        )

        assert second.id == first.id
        assert await session.scalar(select(func.count(PlanRun.id))) == 1
        assert await session.scalar(select(func.count(AgentRun.id))) == 1
    await engine.dispose()


@pytest.mark.asyncio
async def test_scope_generation_reuses_a_successful_run_for_the_same_intake() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    creator_id = uuid.uuid4()
    organization_id = uuid.uuid4()
    async with factory() as session:
        project = Project(
            client_organization_id=organization_id,
            created_by_id=creator_id,
            title="Retry-safe project scope",
            description="Generate one durable scope even when the client retries the request.",
            category="website",
            state=ProjectState.SCOPING.value,
        )
        session.add(project)
        await session.flush()
        session.add(
            AuditEvent(
                actor_id=creator_id,
                organization_id=organization_id,
                action="project.created",
                resource_type="project",
                resource_id=project.id,
                correlation_id=uuid.uuid4(),
                payload={
                    "submitted_snapshot": {
                        "title": project.title,
                        "description": project.description,
                        "category": project.category,
                        "desired_outcome": "Provide a verified public information workflow.",
                        "target_users": "Community members",
                    }
                },
            )
        )
        await session.commit()
        principal = SessionPrincipal(creator_id, organization_id, "client_owner")
        request = Request({"type": "http", "client": ("127.0.0.1", 12345)})
        settings = Settings(
            app_env="test",
            demo_mode=True,
            gemini_provider="fixture",
            database_url="sqlite+aiosqlite:///:memory:",
        )

        first = await run_scope_agent(
            project.id,
            request,
            principal,
            session,
            settings,
            uuid.uuid4(),
        )
        second = await run_scope_agent(
            project.id,
            request,
            principal,
            session,
            settings,
            uuid.uuid4(),
        )

        assert second.id == first.id
        assert await session.scalar(select(func.count(AgentRun.id))) == 1
        assert await session.scalar(select(func.count(ProjectScopeVersion.id))) == 1
    await engine.dispose()
