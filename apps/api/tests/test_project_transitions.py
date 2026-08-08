import uuid

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.auth.service import SessionPrincipal
from app.domain.enums import ProjectState
from app.domain.models import (
    Base,
    Organization,
    OrganizationMembership,
    Project,
    ProjectScopeVersion,
    Quote,
    StaffingRun,
    User,
)
from app.projects.service import TransitionError, TransitionNotFound, transition_project


@pytest.mark.asyncio
async def test_funding_guard_and_idempotent_transition() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    async with factory() as session:
        organization = Organization(name="Operations", slug="operations", kind="platform")
        coordinator = User(email="coordinator@example.test", display_name="Coordinator")
        session.add_all([organization, coordinator])
        await session.flush()
        session.add(
            OrganizationMembership(
                user_id=coordinator.id,
                organization_id=organization.id,
                role="coordinator",
            )
        )
        project = Project(
            client_organization_id=organization.id,
            created_by_id=coordinator.id,
            title="Funded work",
            description="A constrained test project with an explicit deposit guard.",
            category="dashboard",
            state=ProjectState.AWAITING_DEPOSIT.value,
            required_deposit_minor=100_00,
            funded_minor=0,
        )
        session.add(project)
        await session.commit()
        principal = SessionPrincipal(coordinator.id, organization.id, "coordinator")
        with pytest.raises(TransitionError, match="funding"):
            await transition_project(
                session,
                project_id=project.id,
                principal=principal,
                target=ProjectState.STAFFING,
                reason="Attempt before funding",
                expected_version=1,
                idempotency_key="funding-guard-attempt",
                correlation_id=uuid.uuid4(),
            )
        project.funded_minor = 100_00
        await session.commit()
        transitioned = await transition_project(
            session,
            project_id=project.id,
            principal=principal,
            target=ProjectState.STAFFING,
            reason="Verified demo funding",
            expected_version=1,
            idempotency_key="funding-confirmed-once",
            correlation_id=uuid.uuid4(),
        )
        repeated = await transition_project(
            session,
            project_id=project.id,
            principal=principal,
            target=ProjectState.STAFFING,
            reason="Verified demo funding",
            expected_version=1,
            idempotency_key="funding-confirmed-once",
            correlation_id=uuid.uuid4(),
        )
        assert transitioned.state == ProjectState.STAFFING.value
        assert transitioned.version == 2
        assert repeated.id == transitioned.id
    await engine.dispose()


@pytest.mark.asyncio
async def test_staffing_review_requires_completed_matching_evidence() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    async with factory() as session:
        organization = Organization(name="Staffing Ops", slug="staffing-ops", kind="platform")
        coordinator = User(email="staffing-ops@example.test", display_name="Coordinator")
        session.add_all([organization, coordinator])
        await session.flush()
        project = Project(
            client_organization_id=organization.id,
            created_by_id=coordinator.id,
            title="Staffing guarded project",
            description="A project that requires matching evidence before staffing review.",
            category="website",
            state=ProjectState.STAFFING.value,
            required_deposit_minor=10_000,
            funded_minor=10_000,
        )
        session.add(project)
        await session.flush()
        principal = SessionPrincipal(coordinator.id, organization.id, "coordinator")

        with pytest.raises(TransitionError, match="completed staffing run"):
            await transition_project(
                session,
                project_id=project.id,
                principal=principal,
                target=ProjectState.AWAITING_STAFFING_APPROVAL,
                reason="Attempt before deterministic matching.",
                expected_version=1,
                idempotency_key="staffing-evidence-missing",
                correlation_id=uuid.uuid4(),
            )

        scope = ProjectScopeVersion(
            project_id=project.id,
            version=1,
            status="CLIENT_ACCEPTED",
            snapshot={},
        )
        session.add(scope)
        await session.flush()
        session.add(
            StaffingRun(
                project_id=project.id,
                scope_version_id=scope.id,
                status="COMPLETED",
                weights_version="pilot-2026-01",
            )
        )
        await session.commit()
        reviewed = await transition_project(
            session,
            project_id=project.id,
            principal=principal,
            target=ProjectState.AWAITING_STAFFING_APPROVAL,
            reason="Completed matching evidence submitted for review.",
            expected_version=1,
            idempotency_key="staffing-evidence-present",
            correlation_id=uuid.uuid4(),
        )
        assert reviewed.state == ProjectState.AWAITING_STAFFING_APPROVAL.value
    await engine.dispose()


@pytest.mark.asyncio
async def test_transition_idempotency_is_scoped_and_authorized() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    async with factory() as session:
        organization = Organization(name="Tenant A", slug="tenant-a", kind="platform")
        other_organization = Organization(name="Tenant B", slug="tenant-b", kind="platform")
        actor = User(email="actor@example.test", display_name="Actor")
        other_actor = User(email="other@example.test", display_name="Other")
        session.add_all([organization, other_organization, actor, other_actor])
        await session.flush()
        session.add_all(
            [
                OrganizationMembership(
                    user_id=actor.id, organization_id=organization.id, role="coordinator"
                ),
                OrganizationMembership(
                    user_id=other_actor.id,
                    organization_id=other_organization.id,
                    role="coordinator",
                ),
            ]
        )
        project = Project(
            client_organization_id=organization.id,
            created_by_id=actor.id,
            title="Scoped transition",
            description="Transition replay scope test.",
            category="dashboard",
            state=ProjectState.AWAITING_DEPOSIT.value,
            required_deposit_minor=0,
            funded_minor=0,
        )
        other_project = Project(
            client_organization_id=other_organization.id,
            created_by_id=other_actor.id,
            title="Other transition",
            description="Other resource.",
            category="dashboard",
            state=ProjectState.AWAITING_DEPOSIT.value,
            required_deposit_minor=0,
            funded_minor=0,
        )
        session.add_all([project, other_project])
        await session.commit()

        principal = SessionPrincipal(actor.id, organization.id, "coordinator")
        other_principal = SessionPrincipal(other_actor.id, other_organization.id, "client_owner")
        correlation_id = uuid.uuid4()
        await transition_project(
            session,
            project_id=project.id,
            principal=principal,
            target=ProjectState.STAFFING,
            reason="funding confirmed",
            expected_version=1,
            idempotency_key="scoped-transition-key",
            correlation_id=correlation_id,
        )
        replay = await transition_project(
            session,
            project_id=project.id,
            principal=principal,
            target=ProjectState.STAFFING,
            reason="funding confirmed",
            expected_version=1,
            idempotency_key="scoped-transition-key",
            correlation_id=uuid.uuid4(),
        )
        assert replay.id == project.id

        with pytest.raises(TransitionError, match="different transition"):
            await transition_project(
                session,
                project_id=project.id,
                principal=principal,
                target=ProjectState.STAFFING,
                reason="changed payload",
                expected_version=1,
                idempotency_key="scoped-transition-key",
                correlation_id=uuid.uuid4(),
            )
        with pytest.raises(TransitionError, match="replay"):
            await transition_project(
                session,
                project_id=other_project.id,
                principal=other_principal,
                target=ProjectState.STAFFING,
                reason="funding confirmed",
                expected_version=1,
                idempotency_key="scoped-transition-key",
                correlation_id=uuid.uuid4(),
            )
        with pytest.raises(TransitionNotFound, match="Project not found"):
            await transition_project(
                session,
                project_id=project.id,
                principal=other_principal,
                target=ProjectState.STAFFING,
                reason="funding confirmed",
                expected_version=1,
                idempotency_key="cross-tenant-key",
                correlation_id=uuid.uuid4(),
            )
    await engine.dispose()


@pytest.mark.asyncio
async def test_scope_approval_requires_generated_scope_and_quote() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    async with factory() as session:
        organization = Organization(name="Operations", slug="scope-operations", kind="platform")
        coordinator = User(email="scope-coordinator@example.test", display_name="Coordinator")
        session.add_all([organization, coordinator])
        await session.flush()
        project = Project(
            client_organization_id=organization.id,
            created_by_id=coordinator.id,
            title="Approval guarded scope",
            description="A project that cannot bypass scope and quote review gates.",
            category="website",
            state=ProjectState.SCOPING.value,
        )
        session.add(project)
        await session.commit()
        principal = SessionPrincipal(coordinator.id, organization.id, "coordinator")

        with pytest.raises(TransitionError, match="generated scope"):
            await transition_project(
                session,
                project_id=project.id,
                principal=principal,
                target=ProjectState.AWAITING_COORDINATOR_SCOPE_APPROVAL,
                reason="Attempt to bypass scope generation.",
                expected_version=1,
                idempotency_key="missing-scope-proposal",
                correlation_id=uuid.uuid4(),
            )

        scope = ProjectScopeVersion(
            project_id=project.id,
            version=1,
            status="PROPOSED",
            snapshot={},
        )
        session.add(scope)
        await session.commit()
        await transition_project(
            session,
            project_id=project.id,
            principal=principal,
            target=ProjectState.AWAITING_COORDINATOR_SCOPE_APPROVAL,
            reason="Generated scope is ready for coordinator review.",
            expected_version=1,
            idempotency_key="scope-ready-for-review",
            correlation_id=uuid.uuid4(),
        )

        with pytest.raises(TransitionError, match="scope and quote"):
            await transition_project(
                session,
                project_id=project.id,
                principal=principal,
                target=ProjectState.AWAITING_CLIENT_SCOPE_APPROVAL,
                reason="Attempt to bypass deterministic quote creation.",
                expected_version=2,
                idempotency_key="missing-deterministic-quote",
                correlation_id=uuid.uuid4(),
            )

        session.add(
            Quote(
                project_id=project.id,
                scope_version_id=scope.id,
                version=1,
                currency="USD",
                low_minor=10_000,
                base_minor=20_000,
                high_minor=30_000,
                revision_rounds=2,
                formula_version="pilot-2026-01",
                calculation_inputs={},
            )
        )
        await session.commit()
        approved = await transition_project(
            session,
            project_id=project.id,
            principal=principal,
            target=ProjectState.AWAITING_CLIENT_SCOPE_APPROVAL,
            reason="Coordinator approved the scope and quote evidence.",
            expected_version=2,
            idempotency_key="scope-and-quote-approved",
            correlation_id=uuid.uuid4(),
        )
        assert approved.state == ProjectState.AWAITING_CLIENT_SCOPE_APPROVAL.value
        assert scope.status == "COORDINATOR_APPROVED"
    await engine.dispose()
