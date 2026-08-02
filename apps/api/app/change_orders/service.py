import uuid
from dataclasses import dataclass
from typing import Literal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.service import SessionPrincipal
from app.domain.enums import ProjectState, Role
from app.domain.models import (
    Approval,
    AuditEvent,
    ChangeOrder,
    ClientDecision,
    Deliverable,
    OutboxEvent,
    Project,
    ProjectAssignment,
    Quote,
    ScopeChangeRequest,
)
from app.domain.schemas import ChangeOrderCreate, ScopeChangeCreate

Classification = Literal["acceptance_criterion", "included_revision", "defect", "new_scope"]


@dataclass(frozen=True)
class ScopeChangeInput:
    request_text: str
    changes_deliverable: bool
    changes_acceptance_criterion: bool
    adds_integration: bool
    adds_environment: bool
    exceeds_effort_bound: bool
    corrects_verified_defect: bool
    remaining_revision_rounds: int


def classify_scope_change(value: ScopeChangeInput) -> Classification:
    if value.corrects_verified_defect:
        return "defect"
    if any(
        (
            value.changes_deliverable,
            value.changes_acceptance_criterion,
            value.adds_integration,
            value.adds_environment,
            value.exceeds_effort_bound,
        )
    ):
        return "new_scope"
    if value.remaining_revision_rounds > 0:
        return "included_revision"
    return "new_scope"


class ScopeControlError(ValueError):
    pass


class ScopeControlNotFound(ScopeControlError):
    pass


class ScopeControlDenied(ScopeControlError):
    pass


async def _require_project_access(
    session: AsyncSession, principal: SessionPrincipal, project: Project
) -> None:
    if principal.role in {Role.CLIENT_OWNER.value, Role.CLIENT_MEMBER.value}:
        if project.client_organization_id != principal.organization_id:
            raise ScopeControlNotFound("Project not found")
        return
    if principal.role in {Role.COORDINATOR.value, Role.PLATFORM_ADMIN.value}:
        return
    assignment = await session.scalar(
        select(ProjectAssignment.id).where(
            ProjectAssignment.project_id == project.id,
            ProjectAssignment.user_id == principal.user_id,
        )
    )
    if assignment is None:
        raise ScopeControlNotFound("Project not found")


async def request_scope_change(
    session: AsyncSession,
    *,
    project_id: uuid.UUID,
    principal: SessionPrincipal,
    request: ScopeChangeCreate,
) -> ScopeChangeRequest:
    project = await session.scalar(
        select(Project).where(Project.id == project_id).with_for_update()
    )
    if project is None:
        raise ScopeControlNotFound("Project not found")
    await _require_project_access(session, principal, project)
    if project.state != ProjectState.CLIENT_REVIEW.value:
        raise ScopeControlError("Scope changes can be requested during client review")
    quote = await session.scalar(
        select(Quote).where(Quote.project_id == project.id).order_by(Quote.version.desc())
    )
    if quote is None:
        raise ScopeControlError("The accepted quote is missing")
    deliverable = await session.scalar(
        select(Deliverable)
        .where(Deliverable.project_id == project.id)
        .order_by(Deliverable.created_at.desc())
    )
    if deliverable is None:
        raise ScopeControlError("The released deliverable is missing")
    used_revisions = int(
        await session.scalar(
            select(func.count(ClientDecision.id)).where(
                ClientDecision.project_id == project.id,
                ClientDecision.decision == "REVISION_REQUESTED",
            )
        )
        or 0
    )
    remaining_revisions = max(0, quote.revision_rounds - used_revisions)
    classification_input = ScopeChangeInput(
        request_text=request.request_text,
        changes_deliverable=request.changes_deliverable,
        changes_acceptance_criterion=request.changes_acceptance_criterion,
        adds_integration=request.adds_integration,
        adds_environment=request.adds_environment,
        exceeds_effort_bound=request.exceeds_effort_bound,
        corrects_verified_defect=request.corrects_verified_defect,
        remaining_revision_rounds=remaining_revisions,
    )
    classification = classify_scope_change(classification_input)
    record = ScopeChangeRequest(
        project_id=project.id,
        requested_by_id=principal.user_id,
        request_text=request.request_text,
        classification=classification,
        evidence={
            **request.model_dump(mode="json", exclude={"request_text"}),
            "quote_id": str(quote.id),
            "quote_version": quote.version,
            "deliverable_id": str(deliverable.id),
            "deliverable_version": deliverable.version,
            "included_revision_limit": quote.revision_rounds,
            "included_revisions_remaining_before_request": remaining_revisions,
            "classifier_version": "scope-control-v1",
        },
        classified_by_id=None,
    )
    session.add(record)
    await session.flush()
    session.add(
        AuditEvent(
            actor_id=principal.user_id,
            organization_id=principal.organization_id,
            action="scope_change.requested",
            resource_type="scope_change_request",
            resource_id=record.id,
            correlation_id=uuid.uuid4(),
            payload={"classification": classification},
        )
    )
    session.add(
        OutboxEvent(
            event_type="ScopeChangeClassified",
            aggregate_type="scope_change_request",
            aggregate_id=record.id,
            payload={"project_id": str(project.id), "classification": classification},
        )
    )
    await session.commit()
    await session.refresh(record)
    return record


async def list_scope_changes(
    session: AsyncSession,
    *,
    project_id: uuid.UUID,
    principal: SessionPrincipal,
) -> list[ScopeChangeRequest]:
    project = await session.get(Project, project_id)
    if project is None:
        raise ScopeControlNotFound("Project not found")
    await _require_project_access(session, principal, project)
    return list(
        (
            await session.scalars(
                select(ScopeChangeRequest)
                .where(ScopeChangeRequest.project_id == project.id)
                .order_by(ScopeChangeRequest.created_at.desc())
            )
        ).all()
    )


async def list_change_orders(
    session: AsyncSession,
    *,
    project_id: uuid.UUID,
    principal: SessionPrincipal,
) -> list[ChangeOrder]:
    project = await session.get(Project, project_id)
    if project is None:
        raise ScopeControlNotFound("Project not found")
    await _require_project_access(session, principal, project)
    return list(
        (
            await session.scalars(
                select(ChangeOrder)
                .where(ChangeOrder.project_id == project.id)
                .order_by(ChangeOrder.version.desc())
            )
        ).all()
    )


async def create_change_order(
    session: AsyncSession,
    *,
    project_id: uuid.UUID,
    principal: SessionPrincipal,
    request: ChangeOrderCreate,
) -> ChangeOrder:
    project = await session.scalar(
        select(Project).where(Project.id == project_id).with_for_update()
    )
    scope_request = await session.get(ScopeChangeRequest, request.scope_change_request_id)
    if project is None or scope_request is None or scope_request.project_id != project_id:
        raise ScopeControlNotFound("Project or scope-change request not found")
    if principal.role != Role.COORDINATOR.value:
        raise ScopeControlDenied("Coordinator role is required")
    if project.state != ProjectState.CLIENT_REVIEW.value:
        raise ScopeControlError("Change orders are drafted during client review")
    if scope_request.classification != "new_scope":
        raise ScopeControlError("Only new scope can produce a paid change order")
    existing_orders = list(
        (
            await session.scalars(select(ChangeOrder).where(ChangeOrder.project_id == project.id))
        ).all()
    )
    if any(
        item.scope_diff.get("scope_change_request_id") == str(scope_request.id)
        for item in existing_orders
    ):
        raise ScopeControlError("This scope-change request already has a change order")
    recipient_ids = [share.recipient_user_id for share in request.compensation_shares]
    if len(recipient_ids) != len(set(recipient_ids)):
        raise ScopeControlError("Compensation recipients must be unique")
    if sum(share.amount_minor for share in request.compensation_shares) != (
        request.added_compensation_minor
    ):
        raise ScopeControlError("Compensation shares must equal added compensation")
    assigned_ids = set(
        (
            await session.scalars(
                select(ProjectAssignment.user_id).where(
                    ProjectAssignment.project_id == project.id,
                    ProjectAssignment.user_id.in_(recipient_ids),
                )
            )
        ).all()
    )
    if assigned_ids != set(recipient_ids):
        raise ScopeControlError("Every compensation recipient must be assigned to the project")
    order = ChangeOrder(
        project_id=project.id,
        version=max((item.version for item in existing_orders), default=0) + 1,
        state="DRAFT",
        scope_diff={
            **request.scope_diff,
            "scope_change_request_id": str(scope_request.id),
            "compensation_shares": [
                share.model_dump(mode="json") for share in request.compensation_shares
            ],
            "currency": project.currency,
            "project_version": project.version,
        },
        added_compensation_minor=request.added_compensation_minor,
        added_days=request.added_days,
    )
    session.add(order)
    await session.flush()
    session.add(
        AuditEvent(
            actor_id=principal.user_id,
            organization_id=principal.organization_id,
            action="change_order.drafted",
            resource_type="change_order",
            resource_id=order.id,
            correlation_id=uuid.uuid4(),
            payload={
                "version": order.version,
                "added_compensation_minor": order.added_compensation_minor,
                "currency": project.currency,
            },
        )
    )
    await session.commit()
    await session.refresh(order)
    return order


async def decide_change_order(
    session: AsyncSession,
    *,
    project_id: uuid.UUID,
    change_order_id: uuid.UUID,
    principal: SessionPrincipal,
    decision: Literal["ACCEPTED", "REJECTED"],
    reason: str,
) -> ChangeOrder:
    project = await session.scalar(
        select(Project).where(Project.id == project_id).with_for_update()
    )
    order = await session.scalar(
        select(ChangeOrder).where(ChangeOrder.id == change_order_id).with_for_update()
    )
    if project is None or order is None or order.project_id != project_id:
        raise ScopeControlNotFound("Project or change order not found")
    if principal.role != Role.CLIENT_OWNER.value or (
        project.client_organization_id != principal.organization_id
    ):
        raise ScopeControlDenied("Client owner access is required")
    if project.state != ProjectState.CHANGE_ORDER_REVIEW.value:
        raise ScopeControlError("Project is not awaiting a change-order decision")
    if order.state != "DRAFT":
        raise ScopeControlError("Change order has already been decided")
    latest_version = await session.scalar(
        select(func.max(ChangeOrder.version)).where(ChangeOrder.project_id == project.id)
    )
    if order.version != latest_version:
        raise ScopeControlError("Only the latest change order can be decided")
    order.state = decision
    if decision == "ACCEPTED":
        project.required_deposit_minor += order.added_compensation_minor
    session.add(
        Approval(
            project_id=project.id,
            subject_type="change_order",
            subject_id=order.id,
            decision=decision,
            actor_id=principal.user_id,
            reason=reason,
        )
    )
    session.add(
        AuditEvent(
            actor_id=principal.user_id,
            organization_id=principal.organization_id,
            action="change_order.decided",
            resource_type="change_order",
            resource_id=order.id,
            correlation_id=uuid.uuid4(),
            payload={
                "decision": decision,
                "reason": reason,
                "new_required_deposit_minor": project.required_deposit_minor,
            },
        )
    )
    session.add(
        OutboxEvent(
            event_type=f"ChangeOrder{decision.title()}",
            aggregate_type="change_order",
            aggregate_id=order.id,
            payload={"project_id": str(project.id), "decision": decision},
        )
    )
    await session.commit()
    await session.refresh(order)
    return order
