import hashlib
import json
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from pydantic import ValidationError
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.service import SessionPrincipal
from app.domain.enums import ProjectState, Role
from app.domain.models import (
    Approval,
    AssignmentOffer,
    AuditEvent,
    ChangeOrder,
    ClientDecision,
    Deliverable,
    Dispute,
    LeadReview,
    OutboxEvent,
    PayoutAllocation,
    Project,
    ProjectAssignment,
    ProjectScopeVersion,
    ProjectTransition,
    QAReview,
    Quote,
    ScopeChangeRequest,
    StaffingRun,
)
from app.domain.schemas import ProjectCreate
from app.notifications.service import notification_event


@dataclass(frozen=True)
class TransitionRule:
    roles: frozenset[Role]
    event_type: str


RULES: dict[tuple[ProjectState, ProjectState], TransitionRule] = {
    (ProjectState.DRAFT, ProjectState.SCOPING): TransitionRule(
        frozenset({Role.CLIENT_OWNER}), "ProjectSubmitted"
    ),
    (ProjectState.SCOPING, ProjectState.AWAITING_COORDINATOR_SCOPE_APPROVAL): TransitionRule(
        frozenset({Role.COORDINATOR, Role.PLATFORM_ADMIN}), "ScopeRunCompleted"
    ),
    (
        ProjectState.AWAITING_COORDINATOR_SCOPE_APPROVAL,
        ProjectState.AWAITING_CLIENT_SCOPE_APPROVAL,
    ): TransitionRule(frozenset({Role.COORDINATOR}), "ScopeApproved"),
    (
        ProjectState.AWAITING_CLIENT_SCOPE_APPROVAL,
        ProjectState.AWAITING_DEPOSIT,
    ): TransitionRule(frozenset({Role.CLIENT_OWNER}), "QuoteAccepted"),
    (ProjectState.AWAITING_DEPOSIT, ProjectState.STAFFING): TransitionRule(
        frozenset({Role.COORDINATOR}), "FundingConfirmed"
    ),
    (ProjectState.STAFFING, ProjectState.AWAITING_STAFFING_APPROVAL): TransitionRule(
        frozenset({Role.COORDINATOR}), "StaffingRunCompleted"
    ),
    (
        ProjectState.AWAITING_STAFFING_APPROVAL,
        ProjectState.AWAITING_STUDENT_ACCEPTANCE,
    ): TransitionRule(frozenset({Role.COORDINATOR}), "AssignmentOfferCreated"),
    (
        ProjectState.AWAITING_STUDENT_ACCEPTANCE,
        ProjectState.READY_TO_START,
    ): TransitionRule(frozenset({Role.COORDINATOR}), "TeamAccepted"),
    (ProjectState.READY_TO_START, ProjectState.ACTIVE): TransitionRule(
        frozenset({Role.COORDINATOR, Role.TECHNICAL_LEAD}), "ProjectActivated"
    ),
    (ProjectState.ACTIVE, ProjectState.QA_REVIEW): TransitionRule(
        frozenset({Role.STUDENT, Role.TECHNICAL_LEAD}), "DeliverableSubmitted"
    ),
    (ProjectState.QA_REVIEW, ProjectState.AWAITING_RELEASE_APPROVAL): TransitionRule(
        frozenset({Role.TECHNICAL_LEAD, Role.COORDINATOR}), "QARunCompleted"
    ),
    (
        ProjectState.AWAITING_RELEASE_APPROVAL,
        ProjectState.CLIENT_REVIEW,
    ): TransitionRule(frozenset({Role.COORDINATOR}), "ReleaseApproved"),
    (ProjectState.CLIENT_REVIEW, ProjectState.REVISION_REQUESTED): TransitionRule(
        frozenset({Role.CLIENT_OWNER}), "ClientRevisionRequested"
    ),
    (ProjectState.REVISION_REQUESTED, ProjectState.ACTIVE): TransitionRule(
        frozenset({Role.COORDINATOR, Role.TECHNICAL_LEAD}), "RevisionStarted"
    ),
    (ProjectState.CLIENT_REVIEW, ProjectState.CHANGE_ORDER_REVIEW): TransitionRule(
        frozenset({Role.CLIENT_OWNER, Role.COORDINATOR}), "ChangeOrderRequested"
    ),
    (ProjectState.CHANGE_ORDER_REVIEW, ProjectState.ACTIVE): TransitionRule(
        frozenset({Role.COORDINATOR}), "ChangeOrderAccepted"
    ),
    (ProjectState.CHANGE_ORDER_REVIEW, ProjectState.CLIENT_REVIEW): TransitionRule(
        frozenset({Role.CLIENT_OWNER, Role.COORDINATOR}), "ChangeOrderRejected"
    ),
    (ProjectState.CLIENT_REVIEW, ProjectState.ACCEPTED): TransitionRule(
        frozenset({Role.CLIENT_OWNER}), "ClientAccepted"
    ),
    (ProjectState.ACCEPTED, ProjectState.PAYOUT_PENDING): TransitionRule(
        frozenset({Role.COORDINATOR}), "PayoutAllocationApproved"
    ),
    (ProjectState.PAYOUT_PENDING, ProjectState.COMPLETED): TransitionRule(
        frozenset({Role.COORDINATOR}), "PayoutStateChanged"
    ),
}

for _state in ProjectState:
    if _state not in {ProjectState.COMPLETED, ProjectState.CANCELED}:
        RULES[(_state, ProjectState.PAUSED)] = TransitionRule(
            frozenset({Role.COORDINATOR}), "ProjectPaused"
        )
        RULES[(_state, ProjectState.DISPUTED)] = TransitionRule(
            frozenset({Role.CLIENT_OWNER, Role.STUDENT, Role.TECHNICAL_LEAD, Role.COORDINATOR}),
            "DisputeOpened",
        )
        RULES[(_state, ProjectState.CANCELED)] = TransitionRule(
            frozenset({Role.CLIENT_OWNER, Role.COORDINATOR}), "ProjectCanceled"
        )


class TransitionError(ValueError):
    pass


class TransitionNotFound(TransitionError):
    pass


def _transition_request_hash(
    *,
    project_id: uuid.UUID,
    organization_id: uuid.UUID,
    actor_id: uuid.UUID,
    target: ProjectState,
    reason: str,
    expected_version: int,
) -> str:
    canonical = {
        "operation": "project.transition",
        "organization_id": str(organization_id),
        "actor_id": str(actor_id),
        "project_id": str(project_id),
        "target_state": target.value,
        "reason": reason,
        "expected_version": expected_version,
    }
    return hashlib.sha256(
        json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


async def project_intake_snapshot(session: AsyncSession, project: Project) -> ProjectCreate:
    event = await session.scalar(
        select(AuditEvent)
        .where(
            AuditEvent.resource_type == "project",
            AuditEvent.resource_id == project.id,
            AuditEvent.action == "project.created",
        )
        .order_by(AuditEvent.created_at.desc())
    )
    if event is not None:
        submitted = event.payload.get("submitted_snapshot")
        if isinstance(submitted, dict):
            try:
                return ProjectCreate.model_validate(submitted)
            except ValidationError:
                pass
    return ProjectCreate(
        title=project.title,
        description=project.description,
        category=project.category,
        desired_outcome=project.title,
        target_users="Approved client users",
    )


async def transition_project(
    session: AsyncSession,
    *,
    project_id: uuid.UUID,
    principal: SessionPrincipal,
    target: ProjectState,
    reason: str,
    expected_version: int,
    idempotency_key: str,
    correlation_id: uuid.UUID,
) -> Project:
    project = await session.scalar(
        select(Project).where(Project.id == project_id).with_for_update()
    )
    if project is None:
        raise TransitionNotFound("Project not found")
    if principal.role in {Role.CLIENT_OWNER.value, Role.CLIENT_MEMBER.value} and (
        project.client_organization_id != principal.organization_id
    ):
        raise TransitionNotFound("Project not found")
    if principal.role not in {
        Role.CLIENT_OWNER.value,
        Role.CLIENT_MEMBER.value,
        Role.COORDINATOR.value,
        Role.PLATFORM_ADMIN.value,
    }:
        assignment = await session.scalar(
            select(ProjectAssignment.id).where(
                ProjectAssignment.project_id == project.id,
                ProjectAssignment.user_id == principal.user_id,
            )
        )
        if assignment is None:
            raise TransitionNotFound("Project not found")
    request_hash = _transition_request_hash(
        project_id=project.id,
        organization_id=principal.organization_id,
        actor_id=principal.user_id,
        target=target,
        reason=reason,
        expected_version=expected_version,
    )
    existing = await session.scalar(
        select(ProjectTransition).where(ProjectTransition.idempotency_key == idempotency_key)
    )
    if existing is not None:
        replay_rule = RULES.get(
            (ProjectState(existing.previous_state), ProjectState(existing.new_state))
        )
        if replay_rule is None or Role(principal.role) not in replay_rule.roles:
            raise TransitionError("Current role cannot replay this transition")
        if (
            existing.operation != "project.transition"
            or existing.organization_id != principal.organization_id
            or existing.actor_id != principal.user_id
            or existing.project_id != project.id
            or existing.new_state != target.value
            or existing.request_hash != request_hash
        ):
            raise TransitionError("Idempotency key was already used for a different transition")
        return project

    if project.version != expected_version:
        raise TransitionError("Project was changed by another request; refresh and retry")

    current = ProjectState(project.state)
    rule = RULES.get((current, target))
    if rule is None:
        raise TransitionError(f"Transition {current.value} -> {target.value} is not allowed")
    if Role(principal.role) not in rule.roles:
        raise TransitionError("Current role cannot perform this transition")

    if target in {ProjectState.STAFFING, ProjectState.READY_TO_START, ProjectState.ACTIVE}:
        if project.funded_minor < project.required_deposit_minor:
            raise TransitionError("Required funding is not confirmed")
    approval_subject: tuple[str, uuid.UUID] | None = None
    if target is ProjectState.AWAITING_COORDINATOR_SCOPE_APPROVAL:
        scope = await session.scalar(
            select(ProjectScopeVersion)
            .where(ProjectScopeVersion.project_id == project.id)
            .order_by(ProjectScopeVersion.version.desc())
        )
        if scope is None or scope.status != "PROPOSED":
            raise TransitionError("A generated scope proposal is required")
    if target is ProjectState.AWAITING_CLIENT_SCOPE_APPROVAL:
        scope = await session.scalar(
            select(ProjectScopeVersion)
            .where(ProjectScopeVersion.project_id == project.id)
            .order_by(ProjectScopeVersion.version.desc())
        )
        quote = await session.scalar(
            select(Quote).where(Quote.project_id == project.id).order_by(Quote.version.desc())
        )
        if scope is None or scope.status != "PROPOSED" or quote is None:
            raise TransitionError(
                "A proposed scope and quote are required for coordinator approval"
            )
        scope.status = "COORDINATOR_APPROVED"
        scope.immutable_at = datetime.now(UTC)
        approval_subject = ("scope", scope.id)
    if target is ProjectState.AWAITING_STAFFING_APPROVAL:
        staffing = await session.scalar(
            select(StaffingRun)
            .where(StaffingRun.project_id == project.id, StaffingRun.status == "COMPLETED")
            .order_by(StaffingRun.created_at.desc())
        )
        if staffing is None:
            raise TransitionError("A completed staffing run is required")
    if target is ProjectState.AWAITING_DEPOSIT:
        scope = await session.scalar(
            select(ProjectScopeVersion)
            .where(ProjectScopeVersion.project_id == project.id)
            .order_by(ProjectScopeVersion.version.desc())
        )
        quote = await session.scalar(
            select(Quote).where(Quote.project_id == project.id).order_by(Quote.version.desc())
        )
        if scope is None or scope.status != "COORDINATOR_APPROVED" or quote is None:
            raise TransitionError("Coordinator-approved scope and quote are required")
        scope.status = "CLIENT_ACCEPTED"
        quote.status = "CLIENT_ACCEPTED"
        approval_subject = ("scope_and_quote", quote.id)
    if target is ProjectState.AWAITING_STUDENT_ACCEPTANCE:
        staffing = await session.scalar(
            select(StaffingRun)
            .where(StaffingRun.project_id == project.id, StaffingRun.status == "COMPLETED")
            .order_by(StaffingRun.created_at.desc())
        )
        if staffing is None:
            raise TransitionError("A completed staffing run is required")
        approval_subject = ("staffing", staffing.id)
    if target is ProjectState.READY_TO_START:
        open_offers = await session.scalar(
            select(func.count(AssignmentOffer.id)).where(
                AssignmentOffer.project_id == project.id,
                AssignmentOffer.state.in_(["DRAFT", "OFFERED"]),
            )
        )
        student_count = await session.scalar(
            select(func.count(ProjectAssignment.id)).where(
                ProjectAssignment.project_id == project.id,
                ProjectAssignment.role != "technical lead",
            )
        )
        lead_count = await session.scalar(
            select(func.count(ProjectAssignment.id)).where(
                ProjectAssignment.project_id == project.id,
                ProjectAssignment.role == "technical lead",
            )
        )
        if open_offers or not student_count:
            raise TransitionError("All required student offers must be decided and accepted")
        if project.complexity != "LOW" and not lead_count:
            raise TransitionError("This project requires an accepted technical lead")
    if target is ProjectState.ACTIVE:
        plan_approval = await session.scalar(
            select(Approval.id).where(
                Approval.project_id == project.id,
                Approval.subject_type == "plan",
                Approval.decision == "APPROVED",
            )
        )
        if plan_approval is None:
            raise TransitionError("An approved project plan is required before work starts")
    if target is ProjectState.AWAITING_RELEASE_APPROVAL:
        qa_review = await session.scalar(
            select(QAReview)
            .join(Deliverable, Deliverable.id == QAReview.deliverable_id)
            .where(
                Deliverable.project_id == project.id,
                QAReview.status == "COMPLETED",
            )
            .order_by(QAReview.created_at.desc())
        )
        if qa_review is None or qa_review.recommendation != "PASS":
            raise TransitionError("A passing QA review is required")
        if project.complexity != "LOW":
            lead_review = await session.scalar(
                select(LeadReview.id).where(
                    LeadReview.project_id == project.id,
                    LeadReview.review_type == "TECHNICAL_RELEASE",
                    LeadReview.recommendation == "RELEASE",
                    LeadReview.conflict_declared.is_(False),
                )
            )
            if lead_review is None:
                raise TransitionError("A conflict-free lead release review is required")
    scope_change: ScopeChangeRequest | None = None
    if target in {ProjectState.REVISION_REQUESTED, ProjectState.CHANGE_ORDER_REVIEW}:
        scope_change = await session.scalar(
            select(ScopeChangeRequest)
            .where(ScopeChangeRequest.project_id == project.id)
            .order_by(ScopeChangeRequest.created_at.desc())
        )
        if scope_change is None:
            raise TransitionError("A classified scope-change request is required")
        latest_deliverable = await session.scalar(
            select(Deliverable)
            .where(Deliverable.project_id == project.id)
            .order_by(Deliverable.created_at.desc())
        )
        if latest_deliverable is None or scope_change.evidence.get("deliverable_id") != str(
            latest_deliverable.id
        ):
            raise TransitionError("Scope-change request is stale for the released deliverable")
    if target is ProjectState.REVISION_REQUESTED and scope_change is not None:
        if scope_change.classification not in {"included_revision", "defect"}:
            raise TransitionError("New scope requires a paid change order")
    if target is ProjectState.CHANGE_ORDER_REVIEW:
        change_order = await session.scalar(
            select(ChangeOrder)
            .where(ChangeOrder.project_id == project.id)
            .order_by(ChangeOrder.version.desc())
        )
        if (
            scope_change is None
            or scope_change.classification != "new_scope"
            or change_order is None
            or change_order.state != "DRAFT"
            or change_order.scope_diff.get("scope_change_request_id") != str(scope_change.id)
        ):
            raise TransitionError("A current draft change order is required for new scope")
    if current is ProjectState.CHANGE_ORDER_REVIEW and target is ProjectState.ACTIVE:
        accepted_order = await session.scalar(
            select(ChangeOrder)
            .where(ChangeOrder.project_id == project.id)
            .order_by(ChangeOrder.version.desc())
        )
        if accepted_order is None or accepted_order.state != "ACCEPTED":
            raise TransitionError("The latest change order must be accepted")
    if current is ProjectState.CHANGE_ORDER_REVIEW and target is ProjectState.CLIENT_REVIEW:
        rejected_order = await session.scalar(
            select(ChangeOrder)
            .where(ChangeOrder.project_id == project.id)
            .order_by(ChangeOrder.version.desc())
        )
        if rejected_order is None or rejected_order.state != "REJECTED":
            raise TransitionError("The latest change order must be rejected")
    if target is ProjectState.PAYOUT_PENDING:
        approved_allocation = await session.scalar(
            select(PayoutAllocation.id).where(
                PayoutAllocation.project_id == project.id,
                PayoutAllocation.status.in_(["APPROVED", "PAID"]),
            )
        )
        if approved_allocation is None:
            raise TransitionError("An approved payout allocation is required")
    if target is ProjectState.CLIENT_REVIEW:
        approval_subject = ("release", project.id)
    if target is ProjectState.COMPLETED:
        accepted = await session.scalar(
            select(ClientDecision.id).where(
                ClientDecision.project_id == project.id,
                ClientDecision.decision == "ACCEPTED",
            )
        )
        open_disputes = await session.scalar(
            select(func.count(Dispute.id)).where(
                Dispute.project_id == project.id,
                Dispute.state.not_in(["RESOLVED", "CLOSED"]),
            )
        )
        approved_allocation = await session.scalar(
            select(PayoutAllocation.id).where(
                PayoutAllocation.project_id == project.id,
                PayoutAllocation.status == "PAID",
            )
        )
        if (
            project.funded_minor <= 0
            or accepted is None
            or open_disputes
            or approved_allocation is None
        ):
            raise TransitionError(
                "Completion requires client acceptance, confirmed funds, resolved disputes, "
                "and a paid payout allocation"
            )

    project.state = target.value
    project.version += 1
    if approval_subject is not None:
        session.add(
            Approval(
                project_id=project.id,
                subject_type=approval_subject[0],
                subject_id=approval_subject[1],
                decision="APPROVED",
                actor_id=principal.user_id,
                reason=reason,
            )
        )
    if target is ProjectState.ACCEPTED:
        session.add(
            ClientDecision(
                project_id=project.id,
                deliverable_id=None,
                actor_id=principal.user_id,
                decision="ACCEPTED",
                reason=reason,
                revision_round=0,
            )
        )
    if target is ProjectState.REVISION_REQUESTED:
        revision_count = int(
            await session.scalar(
                select(func.count(ClientDecision.id)).where(
                    ClientDecision.project_id == project.id,
                    ClientDecision.decision == "REVISION_REQUESTED",
                )
            )
            or 0
        )
        deliverable = await session.scalar(
            select(Deliverable)
            .where(Deliverable.project_id == project.id)
            .order_by(Deliverable.created_at.desc())
        )
        session.add(
            ClientDecision(
                project_id=project.id,
                deliverable_id=deliverable.id if deliverable else None,
                actor_id=principal.user_id,
                decision="REVISION_REQUESTED",
                reason=reason,
                revision_round=revision_count + 1,
            )
        )
    session.add(
        ProjectTransition(
            project_id=project.id,
            organization_id=principal.organization_id,
            actor_id=principal.user_id,
            operation="project.transition",
            previous_state=current.value,
            new_state=target.value,
            reason=reason,
            correlation_id=correlation_id,
            request_hash=request_hash,
            idempotency_key=idempotency_key,
        )
    )
    session.add(
        AuditEvent(
            actor_id=principal.user_id,
            organization_id=principal.organization_id,
            action="project.transitioned",
            resource_type="project",
            resource_id=project.id,
            correlation_id=correlation_id,
            payload={"from": current.value, "to": target.value, "reason": reason},
        )
    )
    session.add(
        OutboxEvent(
            event_type=rule.event_type,
            aggregate_type="project",
            aggregate_id=project.id,
            payload={"project_id": str(project.id), "state": target.value},
        )
    )
    if project.created_by_id != principal.user_id:
        session.add(
            notification_event(
                recipient_user_id=project.created_by_id,
                category="projects",
                title="Project status changed",
                body=f"{project.title} moved to {target.value.replace('_', ' ').lower()}.",
                resource_path=f"/client/projects/{project.id}",
                correlation_id=correlation_id,
            )
        )
    assignment_recipients = list(
        (
            await session.execute(
                select(ProjectAssignment.user_id, ProjectAssignment.role).where(
                    ProjectAssignment.project_id == project.id,
                    ProjectAssignment.user_id != principal.user_id,
                )
            )
        ).all()
    )
    for user_id, assignment_role in assignment_recipients:
        workspace = "lead" if assignment_role == "technical lead" else "student"
        session.add(
            notification_event(
                recipient_user_id=user_id,
                category="projects",
                title="Project status changed",
                body=f"{project.title} moved to {target.value.replace('_', ' ').lower()}.",
                resource_path=f"/{workspace}/projects/{project.id}",
                correlation_id=correlation_id,
            )
        )
    await session.commit()
    await session.refresh(project)
    return project
