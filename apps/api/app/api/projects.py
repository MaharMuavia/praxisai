import hashlib
import uuid
from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select

from app.agents.guards import StaleAgentResultError, require_current_resource_version
from app.agents.prompts import prompt_for
from app.agents.provider import AgentUnavailableError, input_hash, provider_for
from app.auth.dependencies import (
    DbSession,
    IdempotencyKey,
    Principal,
    correlation_id,
    require_roles,
)
from app.auth.service import SessionPrincipal
from app.config import Settings, get_settings
from app.domain.enums import ProjectState, Role
from app.domain.models import (
    AcceptanceCriterion,
    AgentRun,
    Approval,
    AssignmentOffer,
    AuditEvent,
    AvailabilityWindow,
    CheckIn,
    Deliverable,
    DeliverableArtifact,
    LeadProfile,
    LeadReview,
    Milestone,
    PlanRun,
    Project,
    ProjectAssignment,
    ProjectScopeVersion,
    QAFinding,
    QAReview,
    Quote,
    QuoteLineItem,
    Skill,
    StaffingCandidate,
    StaffingRun,
    StudentProfile,
    StudentSkill,
    Task,
)
from app.domain.policies import evaluate_project
from app.domain.pricing import calculate_quote
from app.domain.schemas import (
    AgentRunView,
    CheckInCreate,
    DecisionRequest,
    DeliverableCreate,
    LeadReviewRequest,
    MultimodalQADraft,
    MultimodalQAInput,
    OfferCreate,
    OfferView,
    PlanDraft,
    PlanInput,
    PlanRunView,
    ProjectCreate,
    ProjectList,
    ProjectView,
    QADraft,
    QAInput,
    QAReviewView,
    QuoteInput,
    QuoteResult,
    ScopeDraft,
    TransitionRequest,
)
from app.projects.service import (
    TransitionError,
    TransitionNotFound,
    project_intake_snapshot,
    transition_project,
)
from app.rate_limits.service import (
    RateLimitExceeded,
    consume_rate_limit,
    opaque_rate_limit_key,
)
from app.staffing.service import CandidateInput, rank_candidates
from app.work_management.service import ensure_acyclic_dependencies

router = APIRouter(prefix="/projects", tags=["projects"])


async def _enforce_rate_limit(
    session: DbSession,
    principal: SessionPrincipal,
    *,
    category: str,
    limit: int,
    window_seconds: int,
) -> None:
    try:
        await consume_rate_limit(
            session,
            raw_key=opaque_rate_limit_key(
                namespace=f"{category}:user",
                identifier=str(principal.user_id),
            ),
            limit=limit,
            window_seconds=window_seconds,
            commit=False,
        )
    except RateLimitExceeded as exc:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, str(exc)) from exc


async def _accessible_project(
    session: DbSession, principal: Principal, project_id: uuid.UUID
) -> Project:
    project = await session.get(Project, project_id)
    if project is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found")
    if principal.role in {Role.CLIENT_OWNER.value, Role.CLIENT_MEMBER.value}:
        allowed = project.client_organization_id == principal.organization_id
    elif principal.role in {Role.COORDINATOR.value, Role.PLATFORM_ADMIN.value}:
        allowed = True
    else:
        assignment = await session.scalar(
            select(ProjectAssignment.id).where(
                ProjectAssignment.project_id == project_id,
                ProjectAssignment.user_id == principal.user_id,
            )
        )
        allowed = assignment is not None
    if not allowed:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found")
    return project


@router.post("", response_model=ProjectView, status_code=status.HTTP_201_CREATED)
async def create_project(
    body: ProjectCreate,
    principal: Annotated[SessionPrincipal, Depends(require_roles(Role.CLIENT_OWNER))],
    session: DbSession,
    settings: Annotated[Settings, Depends(get_settings)],
) -> Project:
    project = Project(
        client_organization_id=principal.organization_id,
        created_by_id=principal.user_id,
        title=body.title,
        description=body.description,
        category=body.category,
        state=ProjectState.DRAFT.value,
        currency="USD",
        is_demo=settings.demo_mode,
    )
    session.add(project)
    await session.flush()
    session.add(
        AuditEvent(
            actor_id=principal.user_id,
            organization_id=principal.organization_id,
            action="project.created",
            resource_type="project",
            resource_id=project.id,
            correlation_id=uuid.uuid4(),
            payload={"submitted_snapshot": body.model_dump(mode="json")},
        )
    )
    await session.commit()
    await session.refresh(project)
    return project


@router.get("", response_model=ProjectList)
async def list_projects(
    principal: Principal,
    session: DbSession,
    cursor: Annotated[uuid.UUID | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 25,
) -> ProjectList:
    query = select(Project).order_by(Project.id).limit(limit + 1)
    if cursor:
        query = query.where(Project.id > cursor)
    if principal.role in {Role.CLIENT_OWNER.value, Role.CLIENT_MEMBER.value}:
        query = query.where(Project.client_organization_id == principal.organization_id)
    elif principal.role not in {Role.COORDINATOR.value, Role.PLATFORM_ADMIN.value}:
        query = query.join(ProjectAssignment).where(ProjectAssignment.user_id == principal.user_id)
    items = list((await session.scalars(query)).all())
    next_cursor = str(items[limit - 1].id) if len(items) > limit else None
    return ProjectList(
        items=[ProjectView.model_validate(item) for item in items[:limit]],
        next_cursor=next_cursor,
    )


@router.get("/{project_id}", response_model=ProjectView)
async def get_project(project_id: uuid.UUID, principal: Principal, session: DbSession) -> Project:
    return await _accessible_project(session, principal, project_id)


@router.post("/{project_id}/transition", response_model=ProjectView)
async def transition(
    project_id: uuid.UUID,
    body: TransitionRequest,
    principal: Principal,
    session: DbSession,
    key: IdempotencyKey,
    request_correlation_id: Annotated[uuid.UUID, Depends(correlation_id)],
) -> Project:
    try:
        return await transition_project(
            session,
            project_id=project_id,
            principal=principal,
            target=body.to_state,
            reason=body.reason,
            expected_version=body.expected_version,
            idempotency_key=key,
            correlation_id=request_correlation_id,
        )
    except TransitionNotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except TransitionError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc


@router.post("/{project_id}/scope-runs", response_model=AgentRunView, status_code=201)
async def run_scope_agent(
    project_id: uuid.UUID,
    principal: Annotated[
        SessionPrincipal,
        Depends(require_roles(Role.CLIENT_OWNER, Role.COORDINATOR, Role.PLATFORM_ADMIN)),
    ],
    session: DbSession,
    settings: Annotated[Settings, Depends(get_settings)],
    request_correlation_id: Annotated[uuid.UUID, Depends(correlation_id)],
) -> AgentRun:
    project = await _accessible_project(session, principal, project_id)
    if project.state != ProjectState.SCOPING.value:
        raise HTTPException(status.HTTP_409_CONFLICT, "Project must be in SCOPING")
    prompt = prompt_for("scoping")
    locked_project = await session.scalar(
        select(Project).where(Project.id == project.id).with_for_update()
    )
    if locked_project is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found")
    project = locked_project
    payload = await project_intake_snapshot(session, project)
    payload_hash = input_hash(payload)
    existing = await session.scalar(
        select(AgentRun)
        .where(
            AgentRun.project_id == project.id,
            AgentRun.agent_name == "scoping",
            AgentRun.prompt_version == prompt.version,
            AgentRun.input_snapshot_hash == payload_hash,
            AgentRun.status == "SUCCEEDED",
        )
        .order_by(AgentRun.created_at.desc())
    )
    if existing is not None:
        return existing
    await _enforce_rate_limit(
        session,
        principal,
        category="agent:scope",
        limit=10,
        window_seconds=60,
    )
    run = AgentRun(
        project_id=project.id,
        agent_name="scoping",
        status="RUNNING",
        model_identifier=None,
        prompt_version=prompt.version,
        input_snapshot_hash=payload_hash,
        input_summary={"title": project.title, "category": project.category},
        output=None,
        validation_status="PENDING",
        latency_ms=None,
        usage=None,
        correlation_id=request_correlation_id,
        is_demo=settings.gemini_provider == "fixture",
        runtime_version="runtime-v1",
        provider=settings.gemini_provider,
        resource_version=project.version,
        human_approval_required=True,
        proposed_actions=[],
        executed_action_evidence=[],
    )
    session.add(run)
    await session.flush()
    try:
        output, metadata = await provider_for(settings).generate_structured(
            agent_name="scoping",
            prompt_version=prompt.version,
            system_instruction=prompt.system_instruction,
            input_payload=payload,
            output_schema=ScopeDraft,
            correlation_id=request_correlation_id,
        )
    except AgentUnavailableError as exc:
        run.status = "FAILED"
        run.validation_status = "NOT_VALIDATED"
        run.error_category = "CONFIGURATION"
        await session.commit()
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc)) from exc

    policy_text = "\n".join(
        [
            payload.description,
            payload.desired_outcome,
            payload.target_users,
            *payload.deliverables,
            *payload.constraints,
        ]
    )
    policy = evaluate_project(
        project.category,
        policy_text,
        output.effort_high_hours,
        payload.data_sensitivity,
    )
    latest_scope_version = await session.scalar(
        select(ProjectScopeVersion.version)
        .where(ProjectScopeVersion.project_id == project.id)
        .order_by(ProjectScopeVersion.version.desc())
    )
    scope_version = ProjectScopeVersion(
        project_id=project.id,
        version=(latest_scope_version or 0) + 1,
        status="PROPOSED",
        snapshot={
            **output.model_dump(mode="json"),
            "eligibility": {
                "eligible": policy.eligible,
                "manual_review": policy.manual_review,
                "reasons": list(policy.reasons),
            },
        },
    )
    session.add(scope_version)
    await session.flush()
    for ordinal, criterion in enumerate(output.acceptance_criteria, start=1):
        session.add(
            AcceptanceCriterion(
                scope_version_id=scope_version.id, ordinal=ordinal, description=criterion
            )
        )
    run.status = "SUCCEEDED"
    run.model_identifier = str(metadata["model"])
    run.output = output.model_dump(mode="json")
    run.validation_status = "VALID"
    run.latency_ms = int(metadata["latency_ms"])
    run.usage = metadata["usage"]
    run.retry_count = metadata["retry_count"]
    project.complexity = output.complexity
    await session.commit()
    await session.refresh(run)
    return run


@router.post("/{project_id}/quotes", response_model=QuoteResult, status_code=201)
async def create_quote(
    project_id: uuid.UUID,
    body: QuoteInput,
    principal: Annotated[SessionPrincipal, Depends(require_roles(Role.COORDINATOR))],
    session: DbSession,
) -> QuoteResult:
    project = await session.get(Project, project_id)
    if project is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found")
    if project.state != ProjectState.AWAITING_COORDINATOR_SCOPE_APPROVAL.value:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Quote creation requires coordinator scope review",
        )
    scope = await session.scalar(
        select(ProjectScopeVersion)
        .where(ProjectScopeVersion.project_id == project.id)
        .order_by(ProjectScopeVersion.version.desc())
    )
    if scope is None or scope.status != "PROPOSED":
        raise HTTPException(status.HTTP_409_CONFLICT, "A proposed scope is required")
    try:
        result = calculate_quote(body)
    except ValueError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc
    existing_versions = list(
        (await session.scalars(select(Quote.version).where(Quote.project_id == project.id))).all()
    )
    quote = Quote(
        project_id=project.id,
        scope_version_id=scope.id,
        version=max(existing_versions, default=0) + 1,
        currency=result.currency,
        low_minor=result.low_minor,
        base_minor=result.base_minor,
        high_minor=result.high_minor,
        revision_rounds=result.revision_rounds,
        formula_version=result.formula_version,
        calculation_inputs=body.model_dump(),
    )
    session.add(quote)
    await session.flush()
    for kind, amount in result.line_items.items():
        session.add(
            QuoteLineItem(
                quote_id=quote.id,
                kind=kind,
                description=kind.replace("_", " "),
                amount_minor=amount,
            )
        )
    project.required_deposit_minor = result.base_minor
    await session.commit()
    return result


@router.post("/{project_id}/staffing-runs", status_code=status.HTTP_201_CREATED)
async def create_staffing_run(
    project_id: uuid.UUID,
    principal: Annotated[SessionPrincipal, Depends(require_roles(Role.COORDINATOR))],
    session: DbSession,
) -> dict[str, object]:
    project = await session.get(Project, project_id)
    if project is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found")
    if project.state != ProjectState.STAFFING.value:
        raise HTTPException(status.HTTP_409_CONFLICT, "Project must be in STAFFING")
    scope = await session.scalar(
        select(ProjectScopeVersion)
        .where(ProjectScopeVersion.project_id == project.id)
        .order_by(ProjectScopeVersion.version.desc())
    )
    if scope is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Approved scope is required")
    existing_run = await session.scalar(
        select(StaffingRun)
        .where(
            StaffingRun.project_id == project.id,
            StaffingRun.scope_version_id == scope.id,
            StaffingRun.status == "COMPLETED",
        )
        .order_by(StaffingRun.created_at.desc())
    )
    if existing_run is not None:
        candidate_count = int(
            await session.scalar(
                select(func.count(StaffingCandidate.id)).where(
                    StaffingCandidate.staffing_run_id == existing_run.id
                )
            )
            or 0
        )
        return {
            "id": existing_run.id,
            "status": existing_run.status,
            "candidate_count": candidate_count,
            "weights_version": existing_run.weights_version,
        }
    profiles = list((await session.scalars(select(StudentProfile))).all())
    candidates: list[CandidateInput] = []
    for profile in profiles:
        availability = await session.scalar(
            select(AvailabilityWindow)
            .where(AvailabilityWindow.student_profile_id == profile.id)
            .order_by(AvailabilityWindow.ends_on.desc())
        )
        skills = (
            await session.execute(
                select(StudentSkill, Skill)
                .join(Skill, Skill.id == StudentSkill.skill_id)
                .where(StudentSkill.student_profile_id == profile.id)
            )
        ).all()
        required_skills = {
            str(item).casefold() for item in scope.snapshot.get("required_skills", [])
        }
        matched = [item for item, skill in skills if skill.name.casefold() in required_skills]
        evidence_count = sum(item.evidence_count for item, _skill in skills)
        skill_fit = round(len(matched) / len(required_skills) * 100) if required_skills else 50
        available_hours = availability.hours_per_week if availability else 0
        candidates.append(
            CandidateInput(
                student_id=str(profile.id),
                active=True,
                eligible=profile.eligible,
                suspended=not profile.eligible,
                conflict=False,
                available_hours=available_hours,
                required_hours=8,
                workload_with_offer=profile.committed_hours + 8,
                workload_cap=profile.workload_cap_hours,
                skill_fit=skill_fit,
                verified_evidence=min(100, evidence_count * 20),
                availability=min(100, available_hours * 5),
                reliability=min(100, 70 + profile.completed_projects * 5),
                complexity_readiness=min(100, 50 + profile.completed_projects * 15),
                evidence_count=evidence_count,
            )
        )
    ranked = rank_candidates(candidates)
    staffing_run = StaffingRun(
        project_id=project.id,
        scope_version_id=scope.id,
        status="COMPLETED",
        weights_version="pilot-2026-01",
    )
    session.add(staffing_run)
    await session.flush()
    for candidate in ranked:
        session.add(
            StaffingCandidate(
                staffing_run_id=staffing_run.id,
                student_profile_id=uuid.UUID(candidate.student_id),
                score_basis_points=candidate.score_basis_points,
                confidence=candidate.confidence,
                components=candidate.components,
                explanation=(
                    f"Job-relevant score with {candidate.evidence_count} evidence records; "
                    f"confidence is {candidate.confidence}."
                ),
            )
        )
    await session.commit()
    return {
        "id": staffing_run.id,
        "status": staffing_run.status,
        "candidate_count": len(ranked),
        "weights_version": staffing_run.weights_version,
    }


@router.post(
    "/{project_id}/assignment-offers",
    response_model=OfferView,
    status_code=status.HTTP_201_CREATED,
)
async def create_assignment_offer(
    project_id: uuid.UUID,
    body: OfferCreate,
    principal: Annotated[SessionPrincipal, Depends(require_roles(Role.COORDINATOR))],
    session: DbSession,
) -> AssignmentOffer:
    project = await session.get(Project, project_id, with_for_update=True)
    if project is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found")
    if project.state != ProjectState.AWAITING_STUDENT_ACCEPTANCE.value:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Offers can only be issued after staffing approval",
        )
    if project.funded_minor < project.required_deposit_minor:
        raise HTTPException(status.HTTP_409_CONFLICT, "Required funding is not confirmed")
    scope = await session.scalar(
        select(ProjectScopeVersion)
        .where(ProjectScopeVersion.project_id == project.id)
        .order_by(ProjectScopeVersion.version.desc())
    )
    quote = await session.scalar(
        select(Quote).where(Quote.project_id == project.id).order_by(Quote.version.desc())
    )
    if scope is None or quote is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Approved scope and quote are required")
    if body.currency != quote.currency:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Offer currency must match quote")
    if body.expected_hours_low > body.expected_hours_high:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Offer hours must be ordered")
    if body.expires_at.tzinfo is None or body.deadline.tzinfo is None:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Offer dates require timezone")
    now = datetime.now(UTC)
    if body.expires_at.astimezone(UTC) <= now or body.deadline.astimezone(UTC) <= now:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY, "Offer dates must be in the future"
        )
    if body.role == "technical lead":
        lead = await session.scalar(
            select(LeadProfile).where(LeadProfile.user_id == body.recipient_user_id)
        )
        if lead is None or not lead.verified:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY, "Recipient is not a verified lead"
            )
        if body.conflict_declared:
            raise HTTPException(status.HTTP_409_CONFLICT, "Declared lead conflict must be resolved")
    else:
        student = await session.scalar(
            select(StudentProfile).where(StudentProfile.user_id == body.recipient_user_id)
        )
        if student is None or not student.eligible:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Recipient is not eligible")
        if student.committed_hours + body.expected_weekly_hours > student.workload_cap_hours:
            raise HTTPException(status.HTTP_409_CONFLICT, "Offer exceeds student workload cap")
    offer = AssignmentOffer(
        project_id=project.id,
        recipient_user_id=body.recipient_user_id,
        role=body.role,
        state="OFFERED",
        terms_snapshot={
            "project_version": project.version,
            "scope_version_id": str(scope.id),
            "quote_id": str(quote.id),
            "role_title": body.role_title,
            "gross_compensation_minor": body.gross_compensation_minor,
            "currency": body.currency,
            "expected_hours": {
                "low": body.expected_hours_low,
                "high": body.expected_hours_high,
            },
            "expected_weekly_hours": body.expected_weekly_hours,
            "deadline": body.deadline.isoformat(),
            "revision_rounds": body.revision_rounds,
            "portfolio_terms": body.portfolio_terms,
            "conflict_declared": body.conflict_declared,
            "decline_reputation_impact": "none",
        },
        expires_at=body.expires_at,
    )
    session.add(offer)
    await session.commit()
    await session.refresh(offer)
    return offer


@router.post("/{project_id}/plan-runs", response_model=PlanRunView, status_code=201)
async def run_planning_agent(
    project_id: uuid.UUID,
    principal: Annotated[
        SessionPrincipal, Depends(require_roles(Role.COORDINATOR, Role.TECHNICAL_LEAD))
    ],
    session: DbSession,
    settings: Annotated[Settings, Depends(get_settings)],
    request_correlation_id: Annotated[uuid.UUID, Depends(correlation_id)],
) -> PlanRun:
    project = await _accessible_project(session, principal, project_id)
    if project.state != ProjectState.READY_TO_START.value:
        raise HTTPException(status.HTTP_409_CONFLICT, "Project must be ready to start")
    prompt = prompt_for("planning")
    scope = await session.scalar(
        select(ProjectScopeVersion)
        .where(
            ProjectScopeVersion.project_id == project.id,
            ProjectScopeVersion.status == "CLIENT_ACCEPTED",
        )
        .order_by(ProjectScopeVersion.version.desc())
    )
    if scope is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "A client-accepted scope is required")
    criteria = list(
        (
            await session.scalars(
                select(AcceptanceCriterion)
                .where(AcceptanceCriterion.scope_version_id == scope.id)
                .order_by(AcceptanceCriterion.ordinal)
            )
        ).all()
    )
    if not criteria:
        raise HTTPException(status.HTTP_409_CONFLICT, "The accepted scope has no criteria")
    payload = PlanInput(
        project_title=project.title,
        scope_version_id=scope.id,
        criterion_count=len(criteria),
    )
    existing_plan = await session.scalar(
        select(PlanRun)
        .where(PlanRun.project_id == project.id, PlanRun.scope_version_id == scope.id)
        .order_by(PlanRun.created_at.desc())
    )
    if (
        existing_plan is not None
        and existing_plan.plan_snapshot.get("project_version") == project.version
        and existing_plan.status in {"PROPOSED", "APPROVED"}
    ):
        return existing_plan
    await _enforce_rate_limit(
        session, principal, category="agent:planning", limit=10, window_seconds=60
    )
    run = AgentRun(
        project_id=project.id,
        agent_name="planning",
        status="RUNNING",
        model_identifier=None,
        prompt_version=prompt.version,
        input_snapshot_hash=input_hash(payload),
        input_summary={
            "scope_version_id": str(scope.id),
            "criterion_count": len(criteria),
        },
        output=None,
        validation_status="PENDING",
        latency_ms=None,
        usage=None,
        correlation_id=request_correlation_id,
        is_demo=settings.gemini_provider == "fixture",
        runtime_version="runtime-v1",
        provider=settings.gemini_provider,
        resource_version=project.version,
        human_approval_required=True,
        proposed_actions=[],
        executed_action_evidence=[],
    )
    session.add(run)
    await session.flush()
    try:
        output, metadata = await provider_for(settings).generate_structured(
            agent_name="planning",
            prompt_version=prompt.version,
            system_instruction=prompt.system_instruction,
            input_payload=payload,
            output_schema=PlanDraft,
            correlation_id=request_correlation_id,
        )
        task_titles = [task.title for milestone in output.milestones for task in milestone.tasks]
        if len(task_titles) != len(set(task_titles)):
            raise ValueError("Plan task titles must be unique")
        known_titles = set(task_titles)
        covered: set[int] = set()
        graph: dict[uuid.UUID, list[uuid.UUID]] = {}
        ids_by_title = {title: uuid.uuid4() for title in task_titles}
        for milestone in output.milestones:
            for task in milestone.tasks:
                if not set(task.dependency_titles) <= known_titles:
                    raise ValueError("Plan references an unknown task dependency")
                if task.title in task.dependency_titles:
                    raise ValueError("A task cannot depend on itself")
                covered.update(task.criterion_ordinals)
                graph[ids_by_title[task.title]] = [
                    ids_by_title[title] for title in task.dependency_titles
                ]
        expected = {criterion.ordinal for criterion in criteria}
        if covered != expected:
            raise ValueError("Plan must cover every acceptance criterion and no unknown criteria")
        ensure_acyclic_dependencies(graph)
    except AgentUnavailableError as exc:
        run.status = "FAILED"
        run.validation_status = "NOT_VALIDATED"
        run.error_category = "CONFIGURATION"
        await session.commit()
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc)) from exc
    except ValueError as exc:
        run.status = "FAILED"
        run.validation_status = "INVALID"
        run.error_category = "SCHEMA_OR_POLICY"
        await session.commit()
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc

    run.status = "SUCCEEDED"
    run.model_identifier = str(metadata["model"])
    run.output = output.model_dump(mode="json")
    run.validation_status = "VALID"
    run.latency_ms = int(metadata["latency_ms"])
    run.usage = metadata["usage"]
    run.retry_count = metadata["retry_count"]
    plan = PlanRun(
        project_id=project.id,
        scope_version_id=scope.id,
        agent_run_id=run.id,
        status="PROPOSED",
        plan_snapshot={
            **output.model_dump(mode="json"),
            "scope_version_id": str(scope.id),
            "project_version": project.version,
        },
    )
    session.add(plan)
    await session.commit()
    await session.refresh(plan)
    return plan


@router.post("/{project_id}/plans/{plan_id}/coordinator-decision", response_model=PlanRunView)
async def decide_plan(
    project_id: uuid.UUID,
    plan_id: uuid.UUID,
    body: DecisionRequest,
    principal: Annotated[SessionPrincipal, Depends(require_roles(Role.COORDINATOR))],
    session: DbSession,
) -> PlanRun:
    project = await session.get(Project, project_id, with_for_update=True)
    plan = await session.get(PlanRun, plan_id, with_for_update=True)
    if project is None or plan is None or plan.project_id != project.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Plan not found")
    if project.state != ProjectState.READY_TO_START.value or plan.status != "PROPOSED":
        raise HTTPException(status.HTTP_409_CONFLICT, "Plan is not awaiting a decision")
    try:
        require_current_resource_version(
            result_version=plan.plan_snapshot.get("project_version"),
            current_version=project.version,
        )
    except StaleAgentResultError as exc:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Plan is stale for the current project"
        ) from exc
    plan.status = body.decision
    session.add(
        Approval(
            project_id=project.id,
            subject_type="plan",
            subject_id=plan.id,
            decision=body.decision,
            actor_id=principal.user_id,
            reason=body.reason,
        )
    )
    if body.decision == "APPROVED":
        milestones = PlanDraft.model_validate(plan.plan_snapshot).milestones
        task_ids = {
            task.title: uuid.uuid4() for milestone in milestones for task in milestone.tasks
        }
        for ordinal, draft_milestone in enumerate(milestones, start=1):
            milestone = Milestone(
                project_id=project.id,
                title=draft_milestone.title,
                ordinal=ordinal,
                due_at=datetime.now(UTC) + timedelta(days=draft_milestone.due_offset_days),
                status="PLANNED",
            )
            session.add(milestone)
            await session.flush()
            for draft_task in draft_milestone.tasks:
                session.add(
                    Task(
                        id=task_ids[draft_task.title],
                        project_id=project.id,
                        milestone_id=milestone.id,
                        title=draft_task.title,
                        definition_of_done=draft_task.definition_of_done,
                        state="BACKLOG",
                        dependency_ids=[
                            str(task_ids[title]) for title in draft_task.dependency_titles
                        ],
                        estimate_hours=draft_task.estimate_hours,
                    )
                )
    session.add(
        AuditEvent(
            actor_id=principal.user_id,
            organization_id=principal.organization_id,
            action="plan.decided",
            resource_type="plan",
            resource_id=plan.id,
            correlation_id=uuid.uuid4(),
            payload={"decision": body.decision, "reason": body.reason},
        )
    )
    await session.commit()
    await session.refresh(plan)
    return plan


@router.post(
    "/{project_id}/deliverables/{deliverable_id}/qa-runs",
    response_model=QAReviewView,
    status_code=201,
)
async def run_qa_agent(
    project_id: uuid.UUID,
    deliverable_id: uuid.UUID,
    principal: Annotated[
        SessionPrincipal, Depends(require_roles(Role.COORDINATOR, Role.TECHNICAL_LEAD))
    ],
    session: DbSession,
    settings: Annotated[Settings, Depends(get_settings)],
    request_correlation_id: Annotated[uuid.UUID, Depends(correlation_id)],
) -> QAReview:
    project = await _accessible_project(session, principal, project_id)
    if project.state != ProjectState.QA_REVIEW.value:
        raise HTTPException(status.HTTP_409_CONFLICT, "Project must be in QA review")
    prompt = prompt_for("qa")
    deliverable = await session.get(Deliverable, deliverable_id)
    if deliverable is None or deliverable.project_id != project.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Deliverable not found")
    artifact = await session.scalar(
        select(DeliverableArtifact)
        .where(DeliverableArtifact.deliverable_id == deliverable.id)
        .order_by(DeliverableArtifact.created_at.desc())
    )
    if artifact is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "An immutable artifact is required")
    if artifact.scan_status == "PENDING":
        raise HTTPException(status.HTTP_409_CONFLICT, "Artifact scanning is not complete")
    scope = await session.scalar(
        select(ProjectScopeVersion)
        .where(
            ProjectScopeVersion.project_id == project.id,
            ProjectScopeVersion.status == "CLIENT_ACCEPTED",
        )
        .order_by(ProjectScopeVersion.version.desc())
    )
    if scope is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Accepted scope is missing")
    criteria = list(
        (
            await session.scalars(
                select(AcceptanceCriterion)
                .where(AcceptanceCriterion.scope_version_id == scope.id)
                .order_by(AcceptanceCriterion.ordinal)
            )
        ).all()
    )
    deterministic = {
        "artifact_hash_present": len(artifact.content_hash) == 64,
        "repository_commit_present": artifact.kind != "repository" or bool(artifact.commit_sha),
        "scanner_clear": artifact.scan_status in {"CLEAN", "NOT_APPLICABLE"},
        "criterion_count": len(criteria),
    }
    deterministic_pass = all(
        bool(value) for key, value in deterministic.items() if key != "criterion_count"
    ) and bool(criteria)
    if not deterministic_pass:
        review = QAReview(
            deliverable_id=deliverable.id,
            artifact_id=artifact.id,
            status="COMPLETED",
            recommendation="CHANGES_REQUIRED",
            deterministic_evidence=deterministic,
            agent_run_id=None,
        )
        session.add(review)
        await session.commit()
        await session.refresh(review)
        return review
    await _enforce_rate_limit(session, principal, category="agent:qa", limit=10, window_seconds=60)
    payload = QAInput(
        artifact_id=artifact.id,
        artifact_kind=artifact.kind,
        artifact_uri=artifact.uri,
        artifact_content_hash=artifact.content_hash,
        acceptance_criteria=[criterion.description for criterion in criteria],
    )
    run = AgentRun(
        project_id=project.id,
        agent_name="qa",
        status="RUNNING",
        model_identifier=None,
        prompt_version=prompt.version,
        input_snapshot_hash=input_hash(payload),
        input_summary={"artifact_id": str(artifact.id), "criterion_count": len(criteria)},
        output=None,
        validation_status="PENDING",
        latency_ms=None,
        usage=None,
        correlation_id=request_correlation_id,
        is_demo=settings.gemini_provider == "fixture",
        runtime_version="runtime-v1",
        provider=settings.gemini_provider,
        resource_version=project.version,
        human_approval_required=True,
        proposed_actions=[],
        executed_action_evidence=[],
    )
    session.add(run)
    await session.flush()
    try:
        output, metadata = await provider_for(settings).generate_structured(
            agent_name="qa",
            prompt_version=prompt.version,
            system_instruction=prompt.system_instruction,
            input_payload=payload,
            output_schema=QADraft,
            correlation_id=request_correlation_id,
        )
        ordinals = [item.criterion_ordinal for item in output.criterion_results]
        if sorted(ordinals) != list(range(1, len(criteria) + 1)):
            raise ValueError("QA output must contain exactly one result per criterion")
        derived_recommendation = (
            "PASS" if all(item.passed for item in output.criterion_results) else "CHANGES_REQUIRED"
        )
        if output.recommendation != derived_recommendation:
            raise ValueError("QA recommendation conflicts with criterion results")
    except AgentUnavailableError as exc:
        run.status = "FAILED"
        run.validation_status = "NOT_VALIDATED"
        run.error_category = "CONFIGURATION"
        await session.commit()
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc)) from exc
    except ValueError as exc:
        run.status = "FAILED"
        run.validation_status = "INVALID"
        run.error_category = "SCHEMA_OR_POLICY"
        await session.commit()
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc
    run.status = "SUCCEEDED"
    run.model_identifier = str(metadata["model"])
    run.output = output.model_dump(mode="json")
    run.validation_status = "VALID"
    run.latency_ms = int(metadata["latency_ms"])
    run.usage = metadata["usage"]
    run.retry_count = metadata["retry_count"]
    review = QAReview(
        deliverable_id=deliverable.id,
        artifact_id=artifact.id,
        status="COMPLETED",
        recommendation=output.recommendation,
        deterministic_evidence=deterministic,
        agent_run_id=run.id,
    )
    session.add(review)
    await session.flush()
    by_ordinal = {criterion.ordinal: criterion for criterion in criteria}
    for result in output.criterion_results:
        session.add(
            QAFinding(
                qa_review_id=review.id,
                criterion_id=by_ordinal[result.criterion_ordinal].id,
                source="agent",
                severity="INFO" if result.passed else "BLOCKING",
                summary=result.summary,
                evidence={**result.evidence, "artifact_content_hash": artifact.content_hash},
            )
        )
    await session.commit()
    await session.refresh(review)
    return review


@router.post(
    "/{project_id}/deliverables/{deliverable_id}/multimodal-qa-runs",
    response_model=AgentRunView,
    status_code=201,
)
async def create_multimodal_qa_run(
    project_id: uuid.UUID,
    deliverable_id: uuid.UUID,
    principal: Annotated[
        SessionPrincipal, Depends(require_roles(Role.COORDINATOR, Role.TECHNICAL_LEAD))
    ],
    session: DbSession,
    settings: Annotated[Settings, Depends(get_settings)],
    request_correlation_id: Annotated[uuid.UUID, Depends(correlation_id)],
) -> AgentRun:
    project = await _accessible_project(session, principal, project_id)
    prompt = prompt_for("multimodal_qa")
    deliverable = await session.get(Deliverable, deliverable_id)
    if deliverable is None or deliverable.project_id != project.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Deliverable not found")
    artifact = await session.scalar(
        select(DeliverableArtifact)
        .where(DeliverableArtifact.deliverable_id == deliverable.id)
        .order_by(DeliverableArtifact.created_at.desc())
    )
    if artifact is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "An immutable artifact is required")
    scope = await session.scalar(
        select(ProjectScopeVersion)
        .where(
            ProjectScopeVersion.project_id == project.id,
            ProjectScopeVersion.status == "CLIENT_ACCEPTED",
        )
        .order_by(ProjectScopeVersion.version.desc())
    )
    if scope is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Accepted scope is missing")
    criteria = list(
        (
            await session.scalars(
                select(AcceptanceCriterion)
                .where(AcceptanceCriterion.scope_version_id == scope.id)
                .order_by(AcceptanceCriterion.ordinal)
            )
        ).all()
    )
    if not criteria:
        raise HTTPException(status.HTTP_409_CONFLICT, "Accepted criteria are required")

    await _enforce_rate_limit(
        session, principal, category="agent:multimodal_qa", limit=10, window_seconds=60
    )
    payload = MultimodalQAInput(
        artifact_id=artifact.id,
        artifact_kind=artifact.kind,
        artifact_uri=artifact.uri,
        artifact_content_hash=artifact.content_hash,
        mime_type="image/png" if artifact.kind == "upload" else "application/octet-stream",
        acceptance_criteria=[criterion.description for criterion in criteria],
        deliverable_title=deliverable.title,
    )
    run = AgentRun(
        project_id=project.id,
        agent_name="multimodal_qa",
        status="RUNNING",
        model_identifier=None,
        prompt_version=prompt.version,
        input_snapshot_hash=input_hash(payload),
        input_summary={
            "artifact_id": str(artifact.id),
            "criterion_count": len(criteria),
            "deliverable_title": deliverable.title,
        },
        output=None,
        validation_status="PENDING",
        latency_ms=None,
        usage=None,
        correlation_id=request_correlation_id,
        is_demo=settings.gemini_provider == "fixture",
        runtime_version="runtime-v1",
        provider=settings.gemini_provider,
        resource_version=project.version,
        human_approval_required=True,
        proposed_actions=[],
        executed_action_evidence=[],
    )
    session.add(run)
    await session.flush()

    try:
        output, metadata = await provider_for(settings).generate_structured(
            agent_name="multimodal_qa",
            prompt_version=prompt.version,
            system_instruction=prompt.system_instruction,
            input_payload=payload,
            output_schema=MultimodalQADraft,
            correlation_id=request_correlation_id,
        )
    except AgentUnavailableError as exc:
        run.status = "FAILED"
        run.validation_status = "NOT_VALIDATED"
        run.error_category = "CONFIGURATION"
        await session.commit()
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc)) from exc
    except Exception as exc:
        run.status = "FAILED"
        run.validation_status = "INVALID"
        run.error_category = "SCHEMA_OR_POLICY"
        await session.commit()
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc

    run.status = "SUCCEEDED"
    run.model_identifier = str(metadata["model"])
    run.output = output.model_dump(mode="json")
    run.validation_status = "VALID"
    run.latency_ms = int(metadata["latency_ms"])
    run.usage = metadata["usage"]
    run.retry_count = metadata["retry_count"]
    await session.commit()
    await session.refresh(run)
    return run


@router.post("/{project_id}/deliverables/{deliverable_id}/lead-review", status_code=201)
async def create_lead_review(
    project_id: uuid.UUID,
    deliverable_id: uuid.UUID,
    body: LeadReviewRequest,
    principal: Annotated[SessionPrincipal, Depends(require_roles(Role.TECHNICAL_LEAD))],
    session: DbSession,
) -> dict[str, object]:
    project = await _accessible_project(session, principal, project_id)
    deliverable = await session.get(Deliverable, deliverable_id)
    if deliverable is None or deliverable.project_id != project.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Deliverable not found")
    if deliverable.submitted_by_id == principal.user_id:
        raise HTTPException(status.HTTP_409_CONFLICT, "Submitter cannot review their own work")
    if body.conflict_declared and body.recommendation == "RELEASE":
        raise HTTPException(status.HTTP_409_CONFLICT, "A conflicted reviewer cannot release work")
    passing_qa = await session.scalar(
        select(QAReview.id).where(
            QAReview.deliverable_id == deliverable.id,
            QAReview.recommendation == "PASS",
            QAReview.status == "COMPLETED",
        )
    )
    if passing_qa is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "A passing QA review is required")
    review = LeadReview(
        project_id=project.id,
        deliverable_id=deliverable.id,
        lead_user_id=principal.user_id,
        review_type="TECHNICAL_RELEASE",
        recommendation=body.recommendation,
        findings={"items": body.findings},
        conflict_declared=body.conflict_declared,
    )
    session.add(review)
    await session.commit()
    await session.refresh(review)
    return {"id": review.id, "recommendation": review.recommendation}


@router.post("/{project_id}/check-ins", status_code=201)
async def create_check_in(
    project_id: uuid.UUID,
    body: CheckInCreate,
    principal: Principal,
    session: DbSession,
) -> dict[str, object]:
    await _accessible_project(session, principal, project_id)
    if principal.role != Role.STUDENT.value:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only assigned students submit check-ins")
    check_in = CheckIn(
        project_id=project_id, student_user_id=principal.user_id, **body.model_dump()
    )
    session.add(check_in)
    await session.commit()
    await session.refresh(check_in)
    return {"id": check_in.id, "created_at": check_in.created_at}


@router.post("/{project_id}/deliverables", status_code=201)
async def create_deliverable(
    project_id: uuid.UUID,
    body: DeliverableCreate,
    principal: Principal,
    session: DbSession,
) -> dict[str, object]:
    project = await _accessible_project(session, principal, project_id)
    if principal.role not in {Role.STUDENT.value, Role.TECHNICAL_LEAD.value}:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "Only assigned delivery team members may submit"
        )
    if project.state != ProjectState.ACTIVE.value:
        raise HTTPException(status.HTTP_409_CONFLICT, "Project is not accepting deliverables")
    await _enforce_rate_limit(
        session, principal, category="artifact:submit", limit=20, window_seconds=60
    )
    deliverable = Deliverable(
        project_id=project.id, submitted_by_id=principal.user_id, title=body.title
    )
    session.add(deliverable)
    await session.flush()
    artifact_uri = str(body.artifact_uri)
    artifact = DeliverableArtifact(
        deliverable_id=deliverable.id,
        kind=body.artifact_kind,
        uri=artifact_uri,
        commit_sha=body.commit_sha,
        content_hash=hashlib.sha256(artifact_uri.encode()).hexdigest(),
        scan_status="NOT_APPLICABLE" if body.artifact_kind != "upload" else "PENDING",
    )
    session.add(artifact)
    await session.commit()
    return {"id": deliverable.id, "artifact_id": artifact.id, "version": deliverable.version}
