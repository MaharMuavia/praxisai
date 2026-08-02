import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.auth.service import SessionPrincipal
from app.domain.models import (
    AcceptanceCriterion,
    Approval,
    AssignmentOffer,
    Base,
    ClientDecision,
    Credential,
    Deliverable,
    DeliverableArtifact,
    Invoice,
    LeadProfile,
    LeadReview,
    Milestone,
    Organization,
    Payout,
    PayoutAllocation,
    Project,
    ProjectAssignment,
    ProjectRisk,
    ProjectScopeVersion,
    ProjectTransition,
    QAReview,
    Quote,
    QuoteLineItem,
    StaffingCandidate,
    StaffingRun,
    StudentProfile,
    Task,
    User,
)
from app.workspaces.service import (
    WorkspaceAccessError,
    WorkspaceNotFound,
    approval_queue,
    client_invoices,
    lead_review_queue,
    participant_earnings,
    project_workspace,
    risk_queue,
    student_credentials,
)


@pytest.mark.asyncio
async def test_role_workspaces_return_only_authorized_operational_records() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    async with factory() as session:
        client_org = Organization(name="Client", slug="workspace-client", kind="client")
        other_org = Organization(name="Other", slug="workspace-other", kind="client")
        ops_org = Organization(name="Ops", slug="workspace-ops", kind="platform")
        client = User(email="workspace-client@example.test", display_name="Client")
        other_client = User(email="workspace-other@example.test", display_name="Other")
        student = User(email="workspace-student@example.test", display_name="Student")
        lead = User(email="workspace-lead@example.test", display_name="Lead")
        coordinator = User(email="workspace-ops@example.test", display_name="Coordinator")
        session.add_all(
            [client_org, other_org, ops_org, client, other_client, student, lead, coordinator]
        )
        await session.flush()
        project = Project(
            client_organization_id=client_org.id,
            created_by_id=client.id,
            title="Authorized project",
            description="A project represented in role-specific workspace queries.",
            category="dashboard",
            state="QA_REVIEW",
        )
        other_project = Project(
            client_organization_id=other_org.id,
            created_by_id=other_client.id,
            title="Other tenant project",
            description="A project that must not appear in the client workspace.",
            category="dashboard",
        )
        session.add_all([project, other_project])
        await session.flush()
        student_profile = StudentProfile(
            user_id=student.id,
            bio="Fictional workspace candidate",
            eligible=True,
            confirmed_18_plus=True,
        )
        lead_profile = LeadProfile(
            user_id=lead.id,
            domains=["accessibility"],
            verified=True,
            workload_cap_hours=10,
            committed_hours=2,
        )
        session.add_all([student_profile, lead_profile])
        await session.flush()
        scope = ProjectScopeVersion(
            project_id=project.id,
            version=1,
            status="CLIENT_ACCEPTED",
            snapshot={
                "normalized_title": "Authorized project",
                "summary": "A constrained scope snapshot.",
            },
            immutable_at=datetime.now(UTC),
        )
        session.add(scope)
        await session.flush()
        session.add(
            AcceptanceCriterion(
                scope_version_id=scope.id,
                ordinal=1,
                description="The authorized workflow is evidenced.",
            )
        )
        quote = Quote(
            project_id=project.id,
            scope_version_id=scope.id,
            version=1,
            currency="USD",
            low_minor=30_000,
            base_minor=40_000,
            high_minor=50_000,
            revision_rounds=2,
            formula_version="pilot-2026-01",
            status="CLIENT_ACCEPTED",
            calculation_inputs={},
        )
        session.add(quote)
        await session.flush()
        session.add(
            QuoteLineItem(
                quote_id=quote.id,
                kind="student_compensation",
                description="student compensation",
                amount_minor=35_000,
            )
        )
        staffing_run = StaffingRun(
            project_id=project.id,
            scope_version_id=scope.id,
            status="COMPLETED",
            weights_version="pilot-2026-01",
        )
        session.add(staffing_run)
        await session.flush()
        session.add(
            StaffingCandidate(
                staffing_run_id=staffing_run.id,
                student_profile_id=student_profile.id,
                score_basis_points=8_200,
                confidence="medium",
                components={"skill_fit": 90},
                explanation="Ranked from job-relevant evidence only.",
            )
        )
        session.add_all(
            [
                Invoice(
                    project_id=project.id,
                    number="INV-CLIENT-001",
                    amount_minor=40_000,
                    currency="USD",
                    status="FUNDED_EXTERNALLY",
                    environment="demo",
                ),
                Invoice(
                    project_id=other_project.id,
                    number="INV-OTHER-001",
                    amount_minor=80_000,
                    currency="USD",
                    status="OPEN",
                    environment="demo",
                ),
                Credential(
                    student_user_id=student.id,
                    project_id=project.id,
                    public_slug="workspace-credential",
                    status="VALID",
                    schema_version="1.0",
                    canonical_payload={},
                    payload_hash="a" * 64,
                    signature="signature",
                    key_identifier="demo-key",
                    consent_snapshot={},
                    issued_at=datetime.now(UTC),
                ),
            ]
        )
        offer = AssignmentOffer(
            project_id=project.id,
            recipient_user_id=lead.id,
            role="technical lead",
            state="ACCEPTED",
            terms_snapshot={},
            expires_at=datetime.now(UTC) + timedelta(days=1),
        )
        session.add(offer)
        await session.flush()
        session.add(
            ProjectAssignment(
                project_id=project.id,
                user_id=lead.id,
                role="technical lead",
                offer_id=offer.id,
            )
        )
        allocation = PayoutAllocation(
            project_id=project.id,
            recipient_user_id=student.id,
            amount_minor=30_000,
            currency="USD",
            status="APPROVED",
        )
        session.add(allocation)
        await session.flush()
        milestone = Milestone(
            project_id=project.id,
            title="Delivery",
            ordinal=1,
            due_at=datetime.now(UTC) + timedelta(days=5),
            status="ACTIVE",
        )
        session.add(milestone)
        await session.flush()
        session.add(
            Task(
                project_id=project.id,
                milestone_id=milestone.id,
                assignee_id=lead.id,
                title="Review evidence",
                definition_of_done="QA and release evidence have been reviewed.",
                state="IN_REVIEW",
                dependency_ids=[],
                estimate_hours=2,
            )
        )
        deliverable = Deliverable(
            project_id=project.id,
            submitted_by_id=student.id,
            title="Release candidate",
            status="ACCEPTED",
            version=1,
        )
        session.add(deliverable)
        await session.flush()
        artifact = DeliverableArtifact(
            deliverable_id=deliverable.id,
            kind="repository",
            uri="https://example.invalid/workspace-artifact",
            commit_sha="a" * 40,
            content_hash="b" * 64,
            scan_status="CLEAN",
        )
        session.add(artifact)
        await session.flush()
        session.add_all(
            [
                Payout(
                    allocation_id=allocation.id,
                    provider_reference="manual-payout-reference",
                    status="RECORDED_EXTERNALLY",
                ),
                LeadReview(
                    project_id=project.id,
                    deliverable_id=deliverable.id,
                    lead_user_id=lead.id,
                    review_type="DELIVERABLE",
                    recommendation="RELEASE",
                    findings={},
                ),
                Approval(
                    project_id=project.id,
                    subject_type="deliverable",
                    subject_id=uuid.uuid4(),
                    decision="PENDING",
                    actor_id=coordinator.id,
                    reason="Awaiting coordinator decision",
                ),
                ProjectRisk(
                    project_id=project.id,
                    source="deterministic",
                    summary="A test risk requiring review",
                    confidence="high",
                    status="OPEN",
                ),
                QAReview(
                    deliverable_id=deliverable.id,
                    artifact_id=artifact.id,
                    status="COMPLETED",
                    recommendation="PASS",
                    deterministic_evidence={"artifact_hash": artifact.content_hash},
                ),
                ClientDecision(
                    project_id=project.id,
                    deliverable_id=deliverable.id,
                    actor_id=client.id,
                    decision="ACCEPTED",
                    reason="Evidence satisfies the fictional client criteria.",
                    revision_round=0,
                ),
                ProjectTransition(
                    project_id=project.id,
                    actor_id=coordinator.id,
                    previous_state="ACTIVE",
                    new_state="QA_REVIEW",
                    reason="Deliverable evidence submitted for QA.",
                    correlation_id=uuid.uuid4(),
                    idempotency_key="workspace-test-transition",
                ),
            ]
        )
        await session.commit()

        client_principal = SessionPrincipal(client.id, client_org.id, "client_owner")
        student_principal = SessionPrincipal(student.id, ops_org.id, "student")
        lead_principal = SessionPrincipal(lead.id, ops_org.id, "technical_lead")
        ops_principal = SessionPrincipal(coordinator.id, ops_org.id, "coordinator")

        invoices = await client_invoices(session, principal=client_principal)
        credentials = await student_credentials(session, principal=student_principal)
        earnings = await participant_earnings(session, principal=student_principal)
        reviews = await lead_review_queue(session, principal=lead_principal)
        approvals = await approval_queue(session, principal=ops_principal)
        risks = await risk_queue(session, principal=ops_principal)
        command_center = await project_workspace(
            session,
            project_id=project.id,
            principal=client_principal,
        )
        operations_command_center = await project_workspace(
            session,
            project_id=project.id,
            principal=ops_principal,
        )

        assert [item.number for item in invoices] == ["INV-CLIENT-001"]
        assert [item.public_slug for item in credentials] == ["workspace-credential"]
        assert earnings[0].payout_status == "RECORDED_EXTERNALLY"
        assert reviews[0].latest_recommendation == "RELEASE"
        assert approvals[0].project_title == project.title
        assert risks[0].summary == "A test risk requiring review"
        assert command_center.tasks[0].title == "Review evidence"
        assert command_center.latest_scope is not None
        assert command_center.latest_scope.acceptance_criteria == [
            "The authorized workflow is evidenced."
        ]
        assert command_center.latest_quote is not None
        assert command_center.latest_quote.line_items[0].amount_minor == 35_000
        assert command_center.latest_staffing is None
        assert operations_command_center.latest_staffing is not None
        assert operations_command_center.latest_staffing.candidates[0].display_name == "Student"
        assert operations_command_center.eligible_leads[0].display_name == "Lead"
        assert operations_command_center.assignment_offers[0].recipient_display_name == "Lead"
        assert command_center.deliverables[0].qa_recommendation == "PASS"
        assert command_center.deliverables[0].artifact_content_hash == "b" * 64
        assert command_center.timeline[0].new_state == "QA_REVIEW"
        with pytest.raises(WorkspaceAccessError):
            await client_invoices(session, principal=student_principal)
        with pytest.raises(WorkspaceNotFound):
            await project_workspace(
                session,
                project_id=project.id,
                principal=SessionPrincipal(other_client.id, other_org.id, "client_owner"),
            )
    await engine.dispose()
