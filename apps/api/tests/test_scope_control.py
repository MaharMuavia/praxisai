import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.auth.service import SessionPrincipal
from app.change_orders.service import (
    create_change_order,
    decide_change_order,
    request_scope_change,
)
from app.domain.enums import ProjectState
from app.domain.models import (
    Approval,
    AssignmentOffer,
    Base,
    ClientDecision,
    Deliverable,
    Organization,
    Project,
    ProjectAssignment,
    ProjectScopeVersion,
    Quote,
    User,
)
from app.domain.schemas import ChangeOrderCreate, CompensationShare, ScopeChangeCreate
from app.projects.service import transition_project


@pytest.mark.asyncio
async def test_paid_change_order_requires_acceptance_and_added_funding() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    async with factory() as session:
        client_org = Organization(name="Client", slug="scope-client", kind="client")
        ops_org = Organization(name="Ops", slug="scope-ops", kind="platform")
        client = User(email="scope-client@example.test", display_name="Client Owner")
        coordinator = User(email="scope-ops@example.test", display_name="Coordinator")
        student = User(email="scope-student@example.test", display_name="Student")
        session.add_all([client_org, ops_org, client, coordinator, student])
        await session.flush()
        project = Project(
            client_organization_id=client_org.id,
            created_by_id=client.id,
            title="Scoped delivery",
            description="A project in client review with an immutable released artifact.",
            category="dashboard",
            state=ProjectState.CLIENT_REVIEW.value,
            required_deposit_minor=100_000,
            funded_minor=100_000,
        )
        session.add(project)
        await session.flush()
        scope = ProjectScopeVersion(
            project_id=project.id,
            version=1,
            status="CLIENT_ACCEPTED",
            snapshot={},
            immutable_at=datetime.now(UTC),
        )
        session.add(scope)
        await session.flush()
        session.add(
            Quote(
                project_id=project.id,
                scope_version_id=scope.id,
                version=1,
                currency="USD",
                low_minor=90_000,
                base_minor=100_000,
                high_minor=120_000,
                revision_rounds=2,
                formula_version="test-v1",
                status="CLIENT_ACCEPTED",
                calculation_inputs={},
            )
        )
        session.add(
            Deliverable(
                project_id=project.id,
                submitted_by_id=student.id,
                title="Released artifact",
                status="RELEASED",
                version=1,
            )
        )
        offer = AssignmentOffer(
            project_id=project.id,
            recipient_user_id=student.id,
            role="student",
            state="ACCEPTED",
            terms_snapshot={"gross_compensation_minor": 70_000},
            expires_at=datetime.now(UTC) + timedelta(days=2),
            decided_at=datetime.now(UTC),
        )
        session.add(offer)
        await session.flush()
        session.add(
            ProjectAssignment(
                project_id=project.id,
                user_id=student.id,
                role="student",
                offer_id=offer.id,
            )
        )
        plan_subject_id = uuid.uuid4()
        session.add(
            Approval(
                project_id=project.id,
                subject_type="plan",
                subject_id=plan_subject_id,
                decision="APPROVED",
                actor_id=coordinator.id,
                reason="Approved execution plan",
            )
        )
        await session.commit()

        client_principal = SessionPrincipal(client.id, client_org.id, "client_owner")
        coordinator_principal = SessionPrincipal(coordinator.id, ops_org.id, "coordinator")
        scope_change = await request_scope_change(
            session,
            project_id=project.id,
            principal=client_principal,
            request=ScopeChangeCreate(
                request_text="Add a second reporting integration and extend delivery.",
                adds_integration=True,
            ),
        )
        assert scope_change.classification == "new_scope"
        order = await create_change_order(
            session,
            project_id=project.id,
            principal=coordinator_principal,
            request=ChangeOrderCreate(
                scope_change_request_id=scope_change.id,
                scope_diff={"added_integration": "Fictional CRM"},
                added_compensation_minor=25_000,
                added_days=5,
                compensation_shares=[
                    CompensationShare(recipient_user_id=student.id, amount_minor=25_000)
                ],
            ),
        )
        await transition_project(
            session,
            project_id=project.id,
            principal=coordinator_principal,
            target=ProjectState.CHANGE_ORDER_REVIEW,
            reason="Send priced change order for client decision",
            expected_version=1,
            idempotency_key="scope-change-review",
            correlation_id=uuid.uuid4(),
        )
        await decide_change_order(
            session,
            project_id=project.id,
            change_order_id=order.id,
            principal=client_principal,
            decision="ACCEPTED",
            reason="The added integration and compensation are accepted.",
        )
        await session.refresh(project)
        assert project.required_deposit_minor == 125_000
        with pytest.raises(ValueError, match="funding"):
            await transition_project(
                session,
                project_id=project.id,
                principal=coordinator_principal,
                target=ProjectState.ACTIVE,
                reason="Attempt before added funding",
                expected_version=2,
                idempotency_key="scope-change-unfunded",
                correlation_id=uuid.uuid4(),
            )
        project.funded_minor = 125_000
        await session.commit()
        resumed = await transition_project(
            session,
            project_id=project.id,
            principal=coordinator_principal,
            target=ProjectState.ACTIVE,
            reason="Added funding confirmed",
            expected_version=2,
            idempotency_key="scope-change-funded",
            correlation_id=uuid.uuid4(),
        )
        assert resumed.state == ProjectState.ACTIVE.value
    await engine.dispose()


@pytest.mark.asyncio
async def test_included_revision_creates_immutable_client_decision() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    async with factory() as session:
        organization = Organization(name="Client", slug="revision-client", kind="client")
        client = User(email="revision@example.test", display_name="Client")
        student = User(email="revision-student@example.test", display_name="Student")
        session.add_all([organization, client, student])
        await session.flush()
        project = Project(
            client_organization_id=organization.id,
            created_by_id=client.id,
            title="Revision project",
            description="A client-reviewed project with one included revision remaining.",
            category="website",
            state=ProjectState.CLIENT_REVIEW.value,
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
            Quote(
                project_id=project.id,
                scope_version_id=scope.id,
                version=1,
                currency="USD",
                low_minor=1,
                base_minor=1,
                high_minor=1,
                revision_rounds=1,
                formula_version="test-v1",
                status="CLIENT_ACCEPTED",
                calculation_inputs={},
            )
        )
        deliverable = Deliverable(
            project_id=project.id,
            submitted_by_id=student.id,
            title="Released site",
            status="RELEASED",
            version=1,
        )
        session.add(deliverable)
        await session.commit()
        principal = SessionPrincipal(client.id, organization.id, "client_owner")
        request = await request_scope_change(
            session,
            project_id=project.id,
            principal=principal,
            request=ScopeChangeCreate(
                request_text="Adjust spacing within the approved responsive layout."
            ),
        )
        assert request.classification == "included_revision"
        await transition_project(
            session,
            project_id=project.id,
            principal=principal,
            target=ProjectState.REVISION_REQUESTED,
            reason="Use the included revision for the approved layout.",
            expected_version=1,
            idempotency_key="included-revision-1",
            correlation_id=uuid.uuid4(),
        )
        decisions = list(
            (
                await session.scalars(
                    select(ClientDecision).where(ClientDecision.project_id == project.id)
                )
            ).all()
        )
        assert len(decisions) == 1
        assert decisions[0].deliverable_id == deliverable.id
        assert decisions[0].revision_round == 1
    await engine.dispose()
