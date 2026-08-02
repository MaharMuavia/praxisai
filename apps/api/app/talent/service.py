import hashlib
import json
import uuid
from datetime import UTC, datetime

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.service import SessionPrincipal
from app.domain.models import (
    AuditEvent,
    Organization,
    Project,
    ProjectOpportunity,
    StudentProfile,
    StudentProposal,
    User,
)
from app.domain.schemas import (
    EmployerOpportunityView,
    OpportunityPublishRequest,
    OpportunityView,
    ProposalDecisionRequest,
    ProposalEvidence,
    ProposalPlanStep,
    StudentProposalCreate,
    StudentProposalView,
)
from app.notifications.service import notification_event


class TalentError(ValueError):
    pass


class TalentNotFound(TalentError):
    pass


def _utc(value: datetime) -> datetime:
    """Normalize database datetimes because SQLite drops timezone metadata in tests."""
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _proposal_view(proposal: StudentProposal, student: User) -> StudentProposalView:
    return StudentProposalView(
        id=proposal.id,
        opportunity_id=proposal.opportunity_id,
        student_user_id=proposal.student_user_id,
        student_display_name=student.display_name,
        cover_note=proposal.cover_note,
        approach=proposal.approach,
        delivery_plan=[ProposalPlanStep.model_validate(step) for step in proposal.delivery_plan],
        relevant_evidence=[
            ProposalEvidence.model_validate(evidence) for evidence in proposal.relevant_evidence
        ],
        proposed_amount_minor=proposal.proposed_amount_minor,
        currency=proposal.currency,
        estimated_days=proposal.estimated_days,
        availability_hours_per_week=proposal.availability_hours_per_week,
        state=proposal.state,
        decision_reason=proposal.decision_reason,
        decided_at=proposal.decided_at,
        created_at=proposal.created_at,
    )


async def _opportunity_view(
    session: AsyncSession,
    *,
    opportunity: ProjectOpportunity,
    student_user_id: uuid.UUID | None,
    include_proposals: bool,
) -> OpportunityView | EmployerOpportunityView:
    project = await session.get(Project, opportunity.project_id)
    if project is None:
        raise TalentNotFound("Opportunity project not found")
    organization = await session.get(Organization, project.client_organization_id)
    if organization is None:
        raise TalentNotFound("Employer organization not found")
    proposal_count = int(
        await session.scalar(
            select(func.count(StudentProposal.id)).where(
                StudentProposal.opportunity_id == opportunity.id
            )
        )
        or 0
    )
    my_proposal: StudentProposalView | None = None
    if student_user_id is not None:
        row = (
            await session.execute(
                select(StudentProposal, User)
                .join(User, User.id == StudentProposal.student_user_id)
                .where(
                    StudentProposal.opportunity_id == opportunity.id,
                    StudentProposal.student_user_id == student_user_id,
                )
            )
        ).first()
        if row is not None:
            my_proposal = _proposal_view(row[0], row[1])
    values = dict(
        id=opportunity.id,
        project_id=opportunity.project_id,
        employer_name=organization.name,
        headline=opportunity.headline,
        brief=opportunity.brief,
        required_skills=opportunity.required_skills,
        nice_to_have_skills=opportunity.nice_to_have_skills,
        deliverables=opportunity.deliverables,
        proposal_requirements=opportunity.proposal_requirements,
        estimated_hours_low=opportunity.estimated_hours_low,
        estimated_hours_high=opportunity.estimated_hours_high,
        budget_minor=opportunity.budget_minor,
        currency=opportunity.currency,
        deadline=opportunity.deadline,
        supervision_level=opportunity.supervision_level,
        status=opportunity.status,
        proposal_count=proposal_count,
        my_proposal=my_proposal,
        created_at=opportunity.created_at,
    )
    if not include_proposals:
        return OpportunityView(**values)
    rows = (
        await session.execute(
            select(StudentProposal, User)
            .join(User, User.id == StudentProposal.student_user_id)
            .where(StudentProposal.opportunity_id == opportunity.id)
            .order_by(StudentProposal.created_at)
        )
    ).all()
    return EmployerOpportunityView(
        **values,
        proposals=[_proposal_view(proposal, student) for proposal, student in rows],
    )


async def list_student_opportunities(
    session: AsyncSession, *, principal: SessionPrincipal
) -> list[OpportunityView]:
    submitted_ids = select(StudentProposal.opportunity_id).where(
        StudentProposal.student_user_id == principal.user_id
    )
    opportunities = list(
        (
            await session.scalars(
                select(ProjectOpportunity)
                .where(
                    or_(
                        ProjectOpportunity.status == "OPEN",
                        ProjectOpportunity.id.in_(submitted_ids),
                    )
                )
                .order_by(ProjectOpportunity.created_at.desc())
            )
        ).all()
    )
    return [
        OpportunityView.model_validate(
            await _opportunity_view(
                session,
                opportunity=opportunity,
                student_user_id=principal.user_id,
                include_proposals=False,
            )
        )
        for opportunity in opportunities
    ]


async def list_student_proposals(
    session: AsyncSession, *, principal: SessionPrincipal
) -> list[StudentProposalView]:
    rows = (
        await session.execute(
            select(StudentProposal, User)
            .join(User, User.id == StudentProposal.student_user_id)
            .where(StudentProposal.student_user_id == principal.user_id)
            .order_by(StudentProposal.created_at.desc())
        )
    ).all()
    return [_proposal_view(proposal, student) for proposal, student in rows]


async def list_employer_opportunities(
    session: AsyncSession, *, principal: SessionPrincipal
) -> list[EmployerOpportunityView]:
    opportunities = list(
        (
            await session.scalars(
                select(ProjectOpportunity)
                .join(Project, Project.id == ProjectOpportunity.project_id)
                .where(Project.client_organization_id == principal.organization_id)
                .order_by(ProjectOpportunity.created_at.desc())
            )
        ).all()
    )
    return [
        EmployerOpportunityView.model_validate(
            await _opportunity_view(
                session,
                opportunity=opportunity,
                student_user_id=None,
                include_proposals=True,
            )
        )
        for opportunity in opportunities
    ]


async def publish_opportunity(
    session: AsyncSession,
    *,
    body: OpportunityPublishRequest,
    principal: SessionPrincipal,
    correlation_id: uuid.UUID,
) -> EmployerOpportunityView:
    project = await session.get(Project, body.project_id, with_for_update=True)
    if project is None or project.client_organization_id != principal.organization_id:
        raise TalentNotFound("Project not found")
    if project.state in {"ACTIVE", "QA_REVIEW", "CLIENT_REVIEW", "COMPLETED", "CANCELED"}:
        raise TalentError("An active or closed project cannot be published as a new opportunity")
    if body.estimated_hours_low > body.estimated_hours_high:
        raise TalentError("Opportunity hours must be ordered low to high")
    if body.currency != project.currency:
        raise TalentError("Opportunity currency must match the project")
    if body.deadline.tzinfo is None or body.deadline.astimezone(UTC) <= datetime.now(UTC):
        raise TalentError("Opportunity deadline must be a future timezone-aware value")
    existing = await session.scalar(
        select(ProjectOpportunity).where(ProjectOpportunity.project_id == project.id)
    )
    if existing is not None:
        raise TalentError("This project already has an opportunity")
    opportunity = ProjectOpportunity(
        project_id=project.id,
        published_by_id=principal.user_id,
        headline=body.headline,
        brief=body.brief,
        required_skills=body.required_skills,
        nice_to_have_skills=body.nice_to_have_skills,
        deliverables=body.deliverables,
        proposal_requirements=body.proposal_requirements,
        estimated_hours_low=body.estimated_hours_low,
        estimated_hours_high=body.estimated_hours_high,
        budget_minor=body.budget_minor,
        currency=body.currency,
        deadline=body.deadline,
        supervision_level=body.supervision_level,
        status="OPEN",
        max_proposals=body.max_proposals,
    )
    session.add(opportunity)
    await session.flush()
    session.add(
        AuditEvent(
            actor_id=principal.user_id,
            organization_id=principal.organization_id,
            action="opportunity.published",
            resource_type="project_opportunity",
            resource_id=opportunity.id,
            correlation_id=correlation_id,
            payload=body.model_dump(mode="json"),
        )
    )
    await session.commit()
    await session.refresh(opportunity)
    return EmployerOpportunityView.model_validate(
        await _opportunity_view(
            session,
            opportunity=opportunity,
            student_user_id=None,
            include_proposals=True,
        )
    )


async def submit_proposal(
    session: AsyncSession,
    *,
    opportunity_id: uuid.UUID,
    body: StudentProposalCreate,
    principal: SessionPrincipal,
    idempotency_key: str,
    correlation_id: uuid.UUID,
) -> StudentProposalView:
    body_hash = hashlib.sha256(
        json.dumps(body.model_dump(mode="json"), sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    replay = await session.scalar(
        select(StudentProposal).where(StudentProposal.submission_idempotency_key == idempotency_key)
    )
    if replay is not None:
        if replay.student_user_id != principal.user_id:
            raise TalentNotFound("Proposal not found")
        if replay.submission_hash != body_hash or replay.opportunity_id != opportunity_id:
            raise TalentError("Idempotency key belongs to a different proposal")
        student = await session.get(User, replay.student_user_id)
        if student is None:
            raise TalentNotFound("Proposal student not found")
        return _proposal_view(replay, student)
    profile = await session.scalar(
        select(StudentProfile).where(StudentProfile.user_id == principal.user_id)
    )
    if profile is None or not profile.eligible or not profile.confirmed_18_plus:
        raise TalentError("An eligible, age-confirmed student profile is required")
    opportunity = await session.get(ProjectOpportunity, opportunity_id, with_for_update=True)
    if opportunity is None:
        raise TalentNotFound("Opportunity not found")
    if opportunity.status != "OPEN" or _utc(opportunity.deadline) <= datetime.now(UTC):
        raise TalentError("Opportunity is no longer accepting proposals")
    proposal_count = int(
        await session.scalar(
            select(func.count(StudentProposal.id)).where(
                StudentProposal.opportunity_id == opportunity.id
            )
        )
        or 0
    )
    if proposal_count >= opportunity.max_proposals:
        raise TalentError("Opportunity has reached its proposal limit")
    existing = await session.scalar(
        select(StudentProposal).where(
            StudentProposal.opportunity_id == opportunity.id,
            StudentProposal.student_user_id == principal.user_id,
        )
    )
    if existing is not None:
        raise TalentError("You already submitted a proposal for this opportunity")
    if body.currency != opportunity.currency:
        raise TalentError("Proposal currency must match the opportunity")
    if body.proposed_amount_minor > opportunity.budget_minor:
        raise TalentError("Proposal amount exceeds the published budget")
    available_hours = profile.workload_cap_hours - profile.committed_hours
    if body.availability_hours_per_week > available_hours:
        raise TalentError("Proposal exceeds your available weekly workload")
    proposal = StudentProposal(
        opportunity_id=opportunity.id,
        student_user_id=principal.user_id,
        cover_note=body.cover_note,
        approach=body.approach,
        delivery_plan=[step.model_dump() for step in body.delivery_plan],
        relevant_evidence=[item.model_dump(mode="json") for item in body.relevant_evidence],
        proposed_amount_minor=body.proposed_amount_minor,
        currency=body.currency,
        estimated_days=body.estimated_days,
        availability_hours_per_week=body.availability_hours_per_week,
        state="SUBMITTED",
        submission_idempotency_key=idempotency_key,
        submission_hash=body_hash,
    )
    session.add(proposal)
    await session.flush()
    project = await session.get(Project, opportunity.project_id)
    if project is None:
        raise TalentNotFound("Opportunity project not found")
    session.add(
        AuditEvent(
            actor_id=principal.user_id,
            organization_id=principal.organization_id,
            action="proposal.submitted",
            resource_type="student_proposal",
            resource_id=proposal.id,
            correlation_id=correlation_id,
            payload={"submission_hash": body_hash, "opportunity_id": str(opportunity.id)},
        )
    )
    session.add(
        notification_event(
            recipient_user_id=project.created_by_id,
            category="offers",
            title="New student proposal",
            body=f"A student submitted a proposal for {opportunity.headline}.",
            resource_path="/client/proposals",
            correlation_id=correlation_id,
        )
    )
    await session.commit()
    student = await session.get(User, principal.user_id)
    if student is None:
        raise TalentNotFound("Student not found")
    return _proposal_view(proposal, student)


async def decide_proposal(
    session: AsyncSession,
    *,
    proposal_id: uuid.UUID,
    body: ProposalDecisionRequest,
    principal: SessionPrincipal,
    idempotency_key: str,
    correlation_id: uuid.UUID,
) -> StudentProposalView:
    replay = await session.scalar(
        select(StudentProposal).where(StudentProposal.decision_idempotency_key == idempotency_key)
    )
    if replay is not None:
        replay_opportunity = await session.get(ProjectOpportunity, replay.opportunity_id)
        replay_project = (
            await session.get(Project, replay_opportunity.project_id)
            if replay_opportunity is not None
            else None
        )
        if (
            replay_project is None
            or replay_project.client_organization_id != principal.organization_id
        ):
            raise TalentNotFound("Proposal not found")
        if replay.id != proposal_id or replay.state != body.decision:
            raise TalentError("Idempotency key belongs to a different proposal decision")
        student = await session.get(User, replay.student_user_id)
        if student is None:
            raise TalentNotFound("Proposal student not found")
        return _proposal_view(replay, student)
    proposal = await session.get(StudentProposal, proposal_id, with_for_update=True)
    if proposal is None:
        raise TalentNotFound("Proposal not found")
    opportunity = await session.get(
        ProjectOpportunity, proposal.opportunity_id, with_for_update=True
    )
    if opportunity is None:
        raise TalentNotFound("Opportunity not found")
    project = await session.get(Project, opportunity.project_id)
    if project is None or project.client_organization_id != principal.organization_id:
        raise TalentNotFound("Proposal not found")
    if proposal.state != "SUBMITTED" or opportunity.status != "OPEN":
        raise TalentError("Proposal is no longer awaiting an employer decision")
    now = datetime.now(UTC)
    proposal.state = body.decision
    proposal.decision_reason = body.reason
    proposal.decided_by_id = principal.user_id
    proposal.decided_at = now
    proposal.decision_idempotency_key = idempotency_key
    if body.decision == "ACCEPTED":
        opportunity.status = "SELECTED"
        competing = list(
            (
                await session.scalars(
                    select(StudentProposal).where(
                        StudentProposal.opportunity_id == opportunity.id,
                        StudentProposal.id != proposal.id,
                        StudentProposal.state == "SUBMITTED",
                    )
                )
            ).all()
        )
        for other in competing:
            other.state = "REJECTED"
            other.decision_reason = "Another proposal was selected for this opportunity."
            other.decided_by_id = principal.user_id
            other.decided_at = now
            session.add(
                notification_event(
                    recipient_user_id=other.student_user_id,
                    category="offers",
                    title="Proposal update",
                    body=(
                        f"Another proposal was selected for {opportunity.headline}. "
                        "This has no reputation impact."
                    ),
                    resource_path="/student/proposals",
                    correlation_id=correlation_id,
                )
            )
    session.add(
        AuditEvent(
            actor_id=principal.user_id,
            organization_id=principal.organization_id,
            action="proposal.decided",
            resource_type="student_proposal",
            resource_id=proposal.id,
            correlation_id=correlation_id,
            payload={"decision": body.decision, "reason": body.reason},
        )
    )
    session.add(
        notification_event(
            recipient_user_id=proposal.student_user_id,
            category="offers",
            title=f"Proposal {body.decision.lower()}",
            body=(
                f"Your proposal for {opportunity.headline} was {body.decision.lower()}. "
                + (
                    "Contracting and funding review must finish before work starts."
                    if body.decision == "ACCEPTED"
                    else "The decision has no reputation impact."
                )
            ),
            resource_path="/student/proposals",
            correlation_id=correlation_id,
        )
    )
    await session.commit()
    student = await session.get(User, proposal.student_user_id)
    if student is None:
        raise TalentNotFound("Proposal student not found")
    return _proposal_view(proposal, student)
