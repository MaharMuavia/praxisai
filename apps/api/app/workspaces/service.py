import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.service import SessionPrincipal
from app.domain.enums import Role
from app.domain.models import (
    AcceptanceCriterion,
    Approval,
    AssignmentOffer,
    ClientDecision,
    Credential,
    CredentialRevocation,
    Deliverable,
    DeliverableArtifact,
    Invoice,
    LeadProfile,
    LeadReview,
    Milestone,
    Payout,
    PayoutAllocation,
    PlanRun,
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
from app.domain.schemas import (
    ApprovalQueueItem,
    ClientInvoiceView,
    DeliverableEvidenceView,
    EarningsItemView,
    LeadCandidateView,
    LeadReviewQueueItem,
    MilestoneView,
    ProjectOfferView,
    ProjectPlanView,
    ProjectTimelineItem,
    ProjectView,
    ProjectWorkspaceView,
    QuoteLineItemView,
    QuoteView,
    RiskQueueItem,
    ScopeVersionView,
    StaffingCandidateView,
    StaffingRunView,
    StudentCredentialView,
    TaskView,
)


class WorkspaceAccessError(ValueError):
    pass


class WorkspaceNotFound(WorkspaceAccessError):
    pass


def _require(principal: SessionPrincipal, *roles: Role) -> None:
    if principal.role not in {role.value for role in roles}:
        raise WorkspaceAccessError("Workspace capability denied")


async def client_invoices(
    session: AsyncSession, *, principal: SessionPrincipal
) -> list[ClientInvoiceView]:
    _require(principal, Role.CLIENT_OWNER, Role.CLIENT_MEMBER)
    rows = (
        await session.execute(
            select(Invoice, Project.title)
            .join(Project, Project.id == Invoice.project_id)
            .where(Project.client_organization_id == principal.organization_id)
            .order_by(Invoice.created_at.desc())
        )
    ).all()
    return [
        ClientInvoiceView(
            id=invoice.id,
            project_id=invoice.project_id,
            project_title=title,
            number=invoice.number,
            amount_minor=invoice.amount_minor,
            currency=invoice.currency,
            status=invoice.status,
            environment=invoice.environment,
            created_at=invoice.created_at,
        )
        for invoice, title in rows
    ]


async def student_credentials(
    session: AsyncSession, *, principal: SessionPrincipal
) -> list[StudentCredentialView]:
    _require(principal, Role.STUDENT)
    rows = (
        await session.execute(
            select(Credential, Project.title, CredentialRevocation.id)
            .join(Project, Project.id == Credential.project_id)
            .outerjoin(
                CredentialRevocation,
                CredentialRevocation.credential_id == Credential.id,
            )
            .where(Credential.student_user_id == principal.user_id)
            .order_by(Credential.issued_at.desc())
        )
    ).all()
    return [
        StudentCredentialView(
            id=credential.id,
            project_id=credential.project_id,
            project_title=title,
            public_slug=credential.public_slug,
            status="REVOKED" if revocation_id is not None else "VALID",
            issued_at=credential.issued_at,
        )
        for credential, title, revocation_id in rows
    ]


async def participant_earnings(
    session: AsyncSession, *, principal: SessionPrincipal
) -> list[EarningsItemView]:
    _require(principal, Role.STUDENT, Role.TECHNICAL_LEAD)
    rows = (
        await session.execute(
            select(PayoutAllocation, Project.title, Payout.status, Payout.failure_reason)
            .join(Project, Project.id == PayoutAllocation.project_id)
            .outerjoin(Payout, Payout.allocation_id == PayoutAllocation.id)
            .where(PayoutAllocation.recipient_user_id == principal.user_id)
            .order_by(PayoutAllocation.created_at.desc())
        )
    ).all()
    return [
        EarningsItemView(
            allocation_id=allocation.id,
            project_id=allocation.project_id,
            project_title=title,
            amount_minor=allocation.amount_minor,
            currency=allocation.currency,
            allocation_status=allocation.status,
            payout_status=payout_status,
            failure_reason=failure_reason,
        )
        for allocation, title, payout_status, failure_reason in rows
    ]


async def lead_review_queue(
    session: AsyncSession, *, principal: SessionPrincipal
) -> list[LeadReviewQueueItem]:
    _require(principal, Role.TECHNICAL_LEAD)
    project_rows = (
        await session.execute(
            select(Project.id, Project.title, Project.state)
            .join(ProjectAssignment, ProjectAssignment.project_id == Project.id)
            .where(
                ProjectAssignment.user_id == principal.user_id,
                ProjectAssignment.role == "technical lead",
            )
            .order_by(Project.updated_at.desc())
        )
    ).all()
    items: list[LeadReviewQueueItem] = []
    for project_id, title, state in project_rows:
        latest = await session.scalar(
            select(LeadReview)
            .where(
                LeadReview.project_id == project_id,
                LeadReview.lead_user_id == principal.user_id,
            )
            .order_by(LeadReview.created_at.desc())
        )
        items.append(
            LeadReviewQueueItem(
                project_id=project_id,
                project_title=title,
                project_state=state,
                latest_recommendation=latest.recommendation if latest else None,
                latest_reviewed_at=latest.created_at if latest else None,
            )
        )
    return items


async def approval_queue(
    session: AsyncSession, *, principal: SessionPrincipal
) -> list[ApprovalQueueItem]:
    _require(principal, Role.COORDINATOR, Role.PLATFORM_ADMIN)
    rows = (
        await session.execute(
            select(Approval, Project.title)
            .join(Project, Project.id == Approval.project_id)
            .where(Approval.decision == "PENDING")
            .order_by(Approval.created_at)
        )
    ).all()
    return [
        ApprovalQueueItem(
            id=approval.id,
            project_id=approval.project_id,
            project_title=title,
            subject_type=approval.subject_type,
            subject_id=approval.subject_id,
            decision=approval.decision,
            reason=approval.reason,
            created_at=approval.created_at,
        )
        for approval, title in rows
    ]


async def risk_queue(session: AsyncSession, *, principal: SessionPrincipal) -> list[RiskQueueItem]:
    _require(principal, Role.COORDINATOR, Role.PLATFORM_ADMIN)
    rows = (
        await session.execute(
            select(ProjectRisk, Project.title)
            .join(Project, Project.id == ProjectRisk.project_id)
            .where(ProjectRisk.status == "OPEN")
            .order_by(ProjectRisk.created_at)
        )
    ).all()
    return [
        RiskQueueItem(
            id=risk.id,
            project_id=risk.project_id,
            project_title=title,
            source=risk.source,
            summary=risk.summary,
            confidence=risk.confidence,
            status=risk.status,
            human_decision=risk.human_decision,
            created_at=risk.created_at,
        )
        for risk, title in rows
    ]


async def project_workspace(
    session: AsyncSession,
    *,
    project_id: uuid.UUID,
    principal: SessionPrincipal,
) -> ProjectWorkspaceView:
    project = await session.get(Project, project_id)
    if project is None:
        raise WorkspaceNotFound("Project not found")
    if principal.role in {Role.CLIENT_OWNER.value, Role.CLIENT_MEMBER.value}:
        allowed = project.client_organization_id == principal.organization_id
    elif principal.role in {Role.COORDINATOR.value, Role.PLATFORM_ADMIN.value}:
        allowed = True
    elif principal.role in {Role.STUDENT.value, Role.TECHNICAL_LEAD.value}:
        allowed = (
            await session.scalar(
                select(ProjectAssignment.id).where(
                    ProjectAssignment.project_id == project.id,
                    ProjectAssignment.user_id == principal.user_id,
                )
            )
            is not None
        )
    else:
        allowed = False
    if not allowed:
        raise WorkspaceNotFound("Project not found")

    latest_scope = await session.scalar(
        select(ProjectScopeVersion)
        .where(ProjectScopeVersion.project_id == project.id)
        .order_by(ProjectScopeVersion.version.desc())
    )
    scope_view: ScopeVersionView | None = None
    if latest_scope is not None:
        criteria = list(
            (
                await session.scalars(
                    select(AcceptanceCriterion)
                    .where(AcceptanceCriterion.scope_version_id == latest_scope.id)
                    .order_by(AcceptanceCriterion.ordinal)
                )
            ).all()
        )
        scope_view = ScopeVersionView(
            id=latest_scope.id,
            version=latest_scope.version,
            status=latest_scope.status,
            snapshot=latest_scope.snapshot,
            acceptance_criteria=[item.description for item in criteria],
            immutable_at=latest_scope.immutable_at,
            created_at=latest_scope.created_at,
        )

    latest_quote = await session.scalar(
        select(Quote).where(Quote.project_id == project.id).order_by(Quote.version.desc())
    )
    quote_view: QuoteView | None = None
    if latest_quote is not None:
        line_items = list(
            (
                await session.scalars(
                    select(QuoteLineItem)
                    .where(QuoteLineItem.quote_id == latest_quote.id)
                    .order_by(QuoteLineItem.created_at, QuoteLineItem.kind)
                )
            ).all()
        )
        quote_view = QuoteView(
            id=latest_quote.id,
            scope_version_id=latest_quote.scope_version_id,
            version=latest_quote.version,
            currency=latest_quote.currency,
            low_minor=latest_quote.low_minor,
            base_minor=latest_quote.base_minor,
            high_minor=latest_quote.high_minor,
            revision_rounds=latest_quote.revision_rounds,
            formula_version=latest_quote.formula_version,
            status=latest_quote.status,
            line_items=[QuoteLineItemView.model_validate(item) for item in line_items],
            created_at=latest_quote.created_at,
        )

    staffing_view: StaffingRunView | None = None
    eligible_leads: list[LeadCandidateView] = []
    assignment_offers: list[ProjectOfferView] = []
    if principal.role in {Role.COORDINATOR.value, Role.PLATFORM_ADMIN.value}:
        latest_staffing = await session.scalar(
            select(StaffingRun)
            .where(StaffingRun.project_id == project.id)
            .order_by(StaffingRun.created_at.desc())
        )
        if latest_staffing is not None:
            candidate_rows = (
                await session.execute(
                    select(StaffingCandidate, StudentProfile, User)
                    .join(
                        StudentProfile,
                        StudentProfile.id == StaffingCandidate.student_profile_id,
                    )
                    .join(User, User.id == StudentProfile.user_id)
                    .where(StaffingCandidate.staffing_run_id == latest_staffing.id)
                    .order_by(StaffingCandidate.score_basis_points.desc())
                )
            ).all()
            staffing_view = StaffingRunView(
                id=latest_staffing.id,
                status=latest_staffing.status,
                weights_version=latest_staffing.weights_version,
                candidates=[
                    StaffingCandidateView(
                        student_profile_id=candidate.student_profile_id,
                        student_user_id=profile.user_id,
                        display_name=user.display_name,
                        score_basis_points=candidate.score_basis_points,
                        confidence=candidate.confidence,
                        components=candidate.components,
                        explanation=candidate.explanation,
                    )
                    for candidate, profile, user in candidate_rows
                ],
                created_at=latest_staffing.created_at,
            )
        lead_rows = (
            await session.execute(
                select(LeadProfile, User)
                .join(User, User.id == LeadProfile.user_id)
                .where(
                    LeadProfile.verified.is_(True),
                    LeadProfile.committed_hours < LeadProfile.workload_cap_hours,
                )
                .order_by(User.display_name)
            )
        ).all()
        eligible_leads = [
            LeadCandidateView(
                user_id=profile.user_id,
                display_name=user.display_name,
                domains=profile.domains,
                available_hours=profile.workload_cap_hours - profile.committed_hours,
            )
            for profile, user in lead_rows
        ]
        offer_rows = (
            await session.execute(
                select(AssignmentOffer, User)
                .join(User, User.id == AssignmentOffer.recipient_user_id)
                .where(AssignmentOffer.project_id == project.id)
                .order_by(AssignmentOffer.created_at)
            )
        ).all()
        assignment_offers = [
            ProjectOfferView(
                id=offer.id,
                recipient_user_id=offer.recipient_user_id,
                recipient_display_name=user.display_name,
                role=offer.role,
                state=offer.state,
                terms_snapshot=offer.terms_snapshot,
                expires_at=offer.expires_at,
                decided_at=offer.decided_at,
            )
            for offer, user in offer_rows
        ]
    latest_plan = await session.scalar(
        select(PlanRun).where(PlanRun.project_id == project.id).order_by(PlanRun.created_at.desc())
    )

    milestones = list(
        (
            await session.scalars(
                select(Milestone)
                .where(Milestone.project_id == project.id)
                .order_by(Milestone.ordinal)
            )
        ).all()
    )
    tasks = list(
        (
            await session.scalars(
                select(Task).where(Task.project_id == project.id).order_by(Task.created_at)
            )
        ).all()
    )
    deliverables = list(
        (
            await session.scalars(
                select(Deliverable)
                .where(Deliverable.project_id == project.id)
                .order_by(Deliverable.created_at.desc())
            )
        ).all()
    )
    deliverable_views: list[DeliverableEvidenceView] = []
    for deliverable in deliverables:
        artifact = await session.scalar(
            select(DeliverableArtifact)
            .where(DeliverableArtifact.deliverable_id == deliverable.id)
            .order_by(DeliverableArtifact.created_at.desc())
        )
        qa_review = await session.scalar(
            select(QAReview)
            .where(QAReview.deliverable_id == deliverable.id)
            .order_by(QAReview.created_at.desc())
        )
        lead_review = await session.scalar(
            select(LeadReview)
            .where(LeadReview.deliverable_id == deliverable.id)
            .order_by(LeadReview.created_at.desc())
        )
        client_decision = await session.scalar(
            select(ClientDecision)
            .where(ClientDecision.deliverable_id == deliverable.id)
            .order_by(ClientDecision.created_at.desc())
        )
        deliverable_views.append(
            DeliverableEvidenceView(
                id=deliverable.id,
                title=deliverable.title,
                status=deliverable.status,
                version=deliverable.version,
                artifact_kind=artifact.kind if artifact else None,
                artifact_content_hash=artifact.content_hash if artifact else None,
                scan_status=artifact.scan_status if artifact else None,
                qa_status=qa_review.status if qa_review else None,
                qa_recommendation=qa_review.recommendation if qa_review else None,
                lead_recommendation=lead_review.recommendation if lead_review else None,
                client_decision=client_decision.decision if client_decision else None,
                created_at=deliverable.created_at,
            )
        )
    risks = list(
        (
            await session.scalars(
                select(ProjectRisk)
                .where(ProjectRisk.project_id == project.id)
                .order_by(ProjectRisk.created_at.desc())
            )
        ).all()
    )
    transitions = list(
        (
            await session.scalars(
                select(ProjectTransition)
                .where(ProjectTransition.project_id == project.id)
                .order_by(ProjectTransition.created_at.desc())
            )
        ).all()
    )
    return ProjectWorkspaceView(
        project=ProjectView.model_validate(project),
        latest_scope=scope_view,
        latest_quote=quote_view,
        latest_staffing=staffing_view,
        eligible_leads=eligible_leads,
        assignment_offers=assignment_offers,
        latest_plan=(
            ProjectPlanView.model_validate(latest_plan) if latest_plan is not None else None
        ),
        milestones=[MilestoneView.model_validate(item) for item in milestones],
        tasks=[TaskView.model_validate(item) for item in tasks],
        deliverables=deliverable_views,
        risks=[
            RiskQueueItem(
                id=risk.id,
                project_id=risk.project_id,
                project_title=project.title,
                source=risk.source,
                summary=risk.summary,
                confidence=risk.confidence,
                status=risk.status,
                human_decision=risk.human_decision,
                created_at=risk.created_at,
            )
            for risk in risks
        ],
        timeline=[
            ProjectTimelineItem(
                id=item.id,
                previous_state=item.previous_state,
                new_state=item.new_state,
                reason=item.reason,
                created_at=item.created_at,
            )
            for item in transitions
        ],
    )
