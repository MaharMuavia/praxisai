import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.auth.service import SessionPrincipal
from app.credentials.lifecycle import issue_project_credential, revoke_project_credential
from app.credentials.service import DemoSigningProvider
from app.domain.enums import ProjectState
from app.domain.models import (
    AssignmentOffer,
    Base,
    ClientDecision,
    ConsentRecord,
    CredentialRevocation,
    Deliverable,
    DeliverableArtifact,
    Organization,
    PortfolioPermission,
    Project,
    ProjectAssignment,
    ProjectTransition,
    QAReview,
    User,
    WorkLog,
)
from app.domain.schemas import CredentialIssueRequest, CredentialSkillEvidence


@pytest.mark.asyncio
async def test_credential_derives_evidence_and_revocation_is_append_only(tmp_path) -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    async with factory() as session:
        client_org = Organization(name="Client", slug="credential-client", kind="client")
        ops_org = Organization(name="Ops", slug="credential-ops", kind="platform")
        client = User(email="credential-client@example.test", display_name="Client")
        coordinator = User(email="credential-ops@example.test", display_name="Coordinator")
        student = User(email="credential-student@example.test", display_name="Student")
        session.add_all([client_org, ops_org, client, coordinator, student])
        await session.flush()
        project = Project(
            client_organization_id=client_org.id,
            created_by_id=client.id,
            title="Private analytics project",
            description="A completed project with persisted credential evidence.",
            category="analytics",
            state=ProjectState.COMPLETED.value,
            is_demo=True,
        )
        session.add(project)
        await session.flush()
        offer = AssignmentOffer(
            project_id=project.id,
            recipient_user_id=student.id,
            role="student developer",
            state="ACCEPTED",
            terms_snapshot={"gross_compensation_minor": 100_000},
            expires_at=datetime.now(UTC) + timedelta(days=1),
            decided_at=datetime.now(UTC),
        )
        session.add(offer)
        await session.flush()
        session.add(
            ProjectAssignment(
                project_id=project.id,
                user_id=student.id,
                role="student developer",
                offer_id=offer.id,
            )
        )
        accepted = ClientDecision(
            project_id=project.id,
            deliverable_id=None,
            actor_id=client.id,
            decision="ACCEPTED",
            reason="Accepted against the approved criteria.",
            revision_round=0,
        )
        session.add(accepted)
        completed = ProjectTransition(
            project_id=project.id,
            actor_id=coordinator.id,
            previous_state=ProjectState.PAYOUT_PENDING.value,
            new_state=ProjectState.COMPLETED.value,
            reason="Payout completed",
            correlation_id=uuid.uuid4(),
            idempotency_key="credential-project-completed",
        )
        session.add(completed)
        deliverable = Deliverable(
            project_id=project.id,
            submitted_by_id=student.id,
            title="Final evidence",
            status="RELEASED",
            version=1,
        )
        session.add(deliverable)
        await session.flush()
        artifact = DeliverableArtifact(
            deliverable_id=deliverable.id,
            kind="repository",
            uri="https://example.test/private-repository",
            commit_sha="a" * 40,
            content_hash="b" * 64,
            scan_status="NOT_APPLICABLE",
        )
        session.add(artifact)
        await session.flush()
        session.add(
            QAReview(
                deliverable_id=deliverable.id,
                artifact_id=artifact.id,
                status="COMPLETED",
                recommendation="PASS",
                deterministic_evidence={"artifact_hash_present": True},
                agent_run_id=None,
            )
        )
        session.add(
            WorkLog(
                project_id=project.id,
                student_user_id=student.id,
                minutes=1_230,
                description="Submitted project work",
                submitted_at=datetime.now(UTC),
            )
        )
        session.add(
            ConsentRecord(
                user_id=student.id,
                consent_type="credential_publication",
                version="demo-1",
                granted=True,
                snapshot={"public_name": True},
            )
        )
        session.add(
            PortfolioPermission(
                project_id=project.id,
                student_user_id=student.id,
                project_title_allowed=False,
                repository_allowed=False,
                consent_snapshot={"repository": False},
            )
        )
        await session.commit()
        principal = SessionPrincipal(coordinator.id, ops_org.id, "coordinator")
        credential = await issue_project_credential(
            session,
            project_id=project.id,
            body=CredentialIssueRequest(
                student_user_id=student.id,
                contribution_summary="Implemented and tested the accepted analytics workflow.",
                skill_evidence=[
                    CredentialSkillEvidence(
                        evidence_id=artifact.id,
                        skill="Testing",
                        criterion="Acceptance criterion 1",
                        summary="Passing QA is bound to the immutable repository artifact.",
                    )
                ],
            ),
            principal=principal,
            signer=DemoSigningProvider(tmp_path / "credential-private.pem"),
            issuer="PraxisAI Demo",
            correlation_id=uuid.uuid4(),
        )

        assert credential.canonical_payload["verified_minutes"] == 1_230
        assert credential.canonical_payload["verified_hours"] == "20.50"
        assert credential.canonical_payload["role"] == "student developer"
        assert credential.canonical_payload["project_title"] == "Private client project"
        assert credential.canonical_payload["public_artifact_references"] == []
        first = await revoke_project_credential(
            session,
            credential_id=credential.id,
            principal=principal,
            reason="The underlying evidence was invalidated after a sustained appeal.",
            idempotency_key="credential-revocation-1",
            correlation_id=uuid.uuid4(),
        )
        repeated = await revoke_project_credential(
            session,
            credential_id=credential.id,
            principal=principal,
            reason="Duplicate delivery",
            idempotency_key="credential-revocation-1",
            correlation_id=uuid.uuid4(),
        )
        await session.refresh(credential)
        count = await session.scalar(select(func.count(CredentialRevocation.id)))
        assert repeated.id == first.id
        assert count == 1
        assert credential.status == "VALID"
        assert credential.revoked_at is None
    await engine.dispose()
