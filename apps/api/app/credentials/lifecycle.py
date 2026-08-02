import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.service import SessionPrincipal
from app.credentials.service import SigningProvider, build_signed_credential
from app.domain.enums import ProjectState, Role
from app.domain.models import (
    ClientDecision,
    ConsentRecord,
    Credential,
    CredentialEvidence,
    CredentialRevocation,
    Deliverable,
    DeliverableArtifact,
    OutboxEvent,
    PortfolioPermission,
    Project,
    ProjectAssignment,
    ProjectTransition,
    QAReview,
    User,
    WorkLog,
)
from app.domain.schemas import CredentialIssueRequest
from app.notifications.service import notification_event


class CredentialLifecycleError(ValueError):
    pass


class CredentialNotFound(CredentialLifecycleError):
    pass


async def issue_project_credential(
    session: AsyncSession,
    *,
    project_id: uuid.UUID,
    body: CredentialIssueRequest,
    principal: SessionPrincipal,
    signer: SigningProvider,
    issuer: str,
    correlation_id: uuid.UUID,
) -> Credential:
    if principal.role != Role.COORDINATOR.value:
        raise CredentialLifecycleError("Coordinator role is required")
    project = await session.get(Project, project_id)
    student = await session.get(User, body.student_user_id)
    if project is None or student is None:
        raise CredentialNotFound("Project or student not found")
    if project.state != ProjectState.COMPLETED.value:
        raise CredentialLifecycleError("Credential issuance requires COMPLETED")
    assignment = await session.scalar(
        select(ProjectAssignment).where(
            ProjectAssignment.project_id == project.id,
            ProjectAssignment.user_id == student.id,
        )
    )
    if assignment is None or assignment.role == "technical lead":
        raise CredentialLifecycleError("Student has no accepted student assignment")
    existing = await session.scalar(
        select(Credential).where(
            Credential.project_id == project.id,
            Credential.student_user_id == student.id,
        )
    )
    if existing is not None:
        raise CredentialLifecycleError("A credential already exists for this student and project")
    consent = await session.scalar(
        select(ConsentRecord)
        .where(
            ConsentRecord.user_id == student.id,
            ConsentRecord.consent_type == "credential_publication",
            ConsentRecord.granted.is_(True),
        )
        .order_by(ConsentRecord.created_at.desc())
    )
    if consent is None:
        raise CredentialLifecycleError("Student publication consent is required")
    permission = await session.scalar(
        select(PortfolioPermission).where(
            PortfolioPermission.project_id == project.id,
            PortfolioPermission.student_user_id == student.id,
        )
    )
    accepted = await session.scalar(
        select(ClientDecision)
        .where(
            ClientDecision.project_id == project.id,
            ClientDecision.decision == "ACCEPTED",
        )
        .order_by(ClientDecision.created_at.desc())
    )
    completed = await session.scalar(
        select(ProjectTransition)
        .where(
            ProjectTransition.project_id == project.id,
            ProjectTransition.new_state == ProjectState.COMPLETED.value,
        )
        .order_by(ProjectTransition.created_at.desc())
    )
    qa_review = await session.scalar(
        select(QAReview)
        .join(Deliverable, Deliverable.id == QAReview.deliverable_id)
        .where(
            Deliverable.project_id == project.id,
            QAReview.status == "COMPLETED",
            QAReview.recommendation == "PASS",
        )
        .order_by(QAReview.created_at.desc())
    )
    verified_minutes = int(
        await session.scalar(
            select(func.coalesce(func.sum(WorkLog.minutes), 0)).where(
                WorkLog.project_id == project.id,
                WorkLog.student_user_id == student.id,
                WorkLog.submitted_at.is_not(None),
            )
        )
        or 0
    )
    if accepted is None or completed is None or qa_review is None or verified_minutes <= 0:
        raise CredentialLifecycleError(
            "Credential evidence requires acceptance, completion, passing QA, "
            "and submitted work logs"
        )
    artifacts = list(
        (
            await session.scalars(
                select(DeliverableArtifact)
                .join(Deliverable, Deliverable.id == DeliverableArtifact.deliverable_id)
                .where(Deliverable.project_id == project.id)
                .order_by(DeliverableArtifact.created_at)
            )
        ).all()
    )
    public_artifacts: list[dict[str, str]] = []
    if permission:
        allowed_kinds = {
            "repository": permission.repository_allowed,
            "deployment": permission.deployment_allowed,
        }
        public_artifacts = [
            {"kind": artifact.kind, "uri": artifact.uri}
            for artifact in artifacts
            if allowed_kinds.get(artifact.kind, False)
        ]
    public_title = (
        project.title
        if permission and permission.project_title_allowed
        else "Private client project"
    )
    now = datetime.now(UTC)
    qa_summary = (
        f"Passing QA review {qa_review.id} is bound to immutable artifact "
        f"{qa_review.artifact_id}; deterministic evidence passed."
    )
    payload, digest, signature, slug = build_signed_credential(
        signer=signer,
        issuer=issuer,
        student_display_name=student.display_name,
        project_title=public_title,
        role=assignment.role,
        contribution_summary=body.contribution_summary,
        skill_evidence=[item.model_dump(mode="json") for item in body.skill_evidence],
        verified_minutes=verified_minutes,
        client_accepted_at=accepted.created_at,
        completed_at=completed.created_at,
        public_artifacts=public_artifacts,
        qa_summary=qa_summary,
        is_demo=project.is_demo,
    )
    credential = Credential(
        student_user_id=student.id,
        project_id=project.id,
        public_slug=slug,
        status="VALID",
        schema_version="1.0",
        canonical_payload=payload,
        payload_hash=digest,
        signature=signature,
        key_identifier=signer.key_identifier,
        consent_snapshot=consent.snapshot,
        issued_at=now,
    )
    session.add(credential)
    await session.flush()
    for item in body.skill_evidence:
        session.add(
            CredentialEvidence(
                credential_id=credential.id,
                evidence_type="verified_skill",
                evidence_id=item.evidence_id,
                public_payload=item.model_dump(mode="json"),
            )
        )
    session.add(
        OutboxEvent(
            event_type="CredentialIssued",
            aggregate_type="credential",
            aggregate_id=credential.id,
            payload={"credential_id": str(credential.id), "public_slug": slug},
        )
    )
    session.add(
        notification_event(
            recipient_user_id=student.id,
            category="credentials",
            title="Credential issued",
            body="Your verified project credential is ready to review and download.",
            resource_path="/student/credentials",
            correlation_id=correlation_id,
        )
    )
    await session.commit()
    await session.refresh(credential)
    return credential


async def revoke_project_credential(
    session: AsyncSession,
    *,
    credential_id: uuid.UUID,
    principal: SessionPrincipal,
    reason: str,
    idempotency_key: str,
    correlation_id: uuid.UUID,
) -> CredentialRevocation:
    if principal.role != Role.COORDINATOR.value:
        raise CredentialLifecycleError("Coordinator role is required")
    existing_key = await session.scalar(
        select(CredentialRevocation).where(CredentialRevocation.idempotency_key == idempotency_key)
    )
    if existing_key is not None:
        if existing_key.credential_id != credential_id:
            raise CredentialLifecycleError("Idempotency key belongs to another credential")
        return existing_key
    credential = await session.get(Credential, credential_id)
    if credential is None:
        raise CredentialNotFound("Credential not found")
    existing_revocation = await session.scalar(
        select(CredentialRevocation).where(CredentialRevocation.credential_id == credential.id)
    )
    if existing_revocation is not None:
        raise CredentialLifecycleError("Credential is already revoked")
    revocation = CredentialRevocation(
        credential_id=credential.id,
        revoked_by_id=principal.user_id,
        reason=reason,
        idempotency_key=idempotency_key,
        revoked_at=datetime.now(UTC),
    )
    session.add(revocation)
    await session.flush()
    session.add(
        OutboxEvent(
            event_type="CredentialRevoked",
            aggregate_type="credential_revocation",
            aggregate_id=revocation.id,
            payload={
                "credential_id": str(credential.id),
                "revocation_id": str(revocation.id),
            },
        )
    )
    session.add(
        notification_event(
            recipient_user_id=credential.student_user_id,
            category="credentials",
            title="Credential revoked",
            body=(
                "A coordinator revoked a project credential. "
                "The reason is available in the credential record."
            ),
            resource_path="/student/credentials",
            correlation_id=correlation_id,
        )
    )
    await session.commit()
    await session.refresh(revocation)
    return revocation
