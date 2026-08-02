import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import func, select

from app.auth.dependencies import DbSession, IdempotencyKey, require_roles
from app.auth.service import SessionPrincipal
from app.billing.service import (
    FundingError,
    FundingNotFound,
    PayoutError,
    PayoutNotFound,
    record_external_payout,
    record_manual_funding,
)
from app.domain.enums import Role
from app.domain.models import (
    AssignmentOffer,
    AuditEvent,
    ChangeOrder,
    OutboxEvent,
    Payout,
    PayoutAllocation,
    Project,
    ProjectAssignment,
)
from app.domain.schemas import (
    ExternalFundingRequest,
    ExternalPayoutRequest,
    PayoutAllocationCreate,
    PayoutAllocationView,
    PayoutRecordView,
)
from app.notifications.service import notification_event

router = APIRouter(tags=["billing"])


@router.post("/ops/projects/{project_id}/external-funding", status_code=status.HTTP_204_NO_CONTENT)
async def record_external_funding(
    project_id: uuid.UUID,
    body: ExternalFundingRequest,
    principal: Annotated[SessionPrincipal, Depends(require_roles(Role.COORDINATOR))],
    session: DbSession,
    key: IdempotencyKey,
    request: Request,
) -> None:
    try:
        await record_manual_funding(
            session,
            project_id=project_id,
            body=body,
            principal=principal,
            idempotency_key=key,
            correlation_id=request.state.correlation_id,
        )
    except FundingNotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except FundingError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc


@router.post(
    "/ops/projects/{project_id}/payout-allocations",
    response_model=PayoutAllocationView,
    status_code=status.HTTP_201_CREATED,
)
async def create_payout_allocation(
    project_id: uuid.UUID,
    body: PayoutAllocationCreate,
    principal: Annotated[SessionPrincipal, Depends(require_roles(Role.COORDINATOR))],
    session: DbSession,
) -> PayoutAllocation:
    project = await session.get(Project, project_id, with_for_update=True)
    if project is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found")
    if project.state != "ACCEPTED":
        raise HTTPException(status.HTTP_409_CONFLICT, "Client acceptance is required")
    if body.currency != project.currency:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Currency mismatch")
    assignment = await session.scalar(
        select(ProjectAssignment)
        .join(AssignmentOffer, AssignmentOffer.id == ProjectAssignment.offer_id)
        .where(
            ProjectAssignment.project_id == project.id,
            ProjectAssignment.user_id == body.recipient_user_id,
        )
    )
    if assignment is None:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Recipient is not assigned")
    offer = await session.get(AssignmentOffer, assignment.offer_id)
    if offer is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Accepted offer snapshot is missing")
    offered = int(offer.terms_snapshot.get("gross_compensation_minor", 0))
    accepted_change_orders = list(
        (
            await session.scalars(
                select(ChangeOrder).where(
                    ChangeOrder.project_id == project.id,
                    ChangeOrder.state == "ACCEPTED",
                )
            )
        ).all()
    )
    added_entitlement = 0
    for order in accepted_change_orders:
        raw_shares = order.scope_diff.get("compensation_shares", [])
        if not isinstance(raw_shares, list):
            raise HTTPException(
                status.HTTP_409_CONFLICT, "Accepted change-order compensation is malformed"
            )
        for raw_share in raw_shares:
            if not isinstance(raw_share, dict):
                raise HTTPException(
                    status.HTTP_409_CONFLICT, "Accepted change-order compensation is malformed"
                )
            if raw_share.get("recipient_user_id") == str(body.recipient_user_id):
                amount = raw_share.get("amount_minor")
                if not isinstance(amount, int) or amount <= 0:
                    raise HTTPException(
                        status.HTTP_409_CONFLICT,
                        "Accepted change-order compensation is malformed",
                    )
                added_entitlement += amount
    recipient_allocated = int(
        await session.scalar(
            select(func.coalesce(func.sum(PayoutAllocation.amount_minor), 0)).where(
                PayoutAllocation.project_id == project.id,
                PayoutAllocation.recipient_user_id == body.recipient_user_id,
                PayoutAllocation.status.not_in(["REJECTED", "REVERSED"]),
            )
        )
        or 0
    )
    if recipient_allocated + body.amount_minor > offered + added_entitlement:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "Allocations exceed accepted offer and change-order compensation",
        )
    allocated = int(
        await session.scalar(
            select(func.coalesce(func.sum(PayoutAllocation.amount_minor), 0)).where(
                PayoutAllocation.project_id == project.id,
                PayoutAllocation.status.not_in(["REJECTED", "REVERSED"]),
            )
        )
        or 0
    )
    if allocated + body.amount_minor > project.funded_minor:
        raise HTTPException(status.HTTP_409_CONFLICT, "Allocations exceed confirmed funds")
    allocation = PayoutAllocation(
        project_id=project.id,
        recipient_user_id=body.recipient_user_id,
        amount_minor=body.amount_minor,
        currency=body.currency,
        status="PENDING",
    )
    session.add(allocation)
    await session.flush()
    session.add(
        AuditEvent(
            actor_id=principal.user_id,
            organization_id=principal.organization_id,
            action="payout_allocation.created",
            resource_type="payout_allocation",
            resource_id=allocation.id,
            correlation_id=uuid.uuid4(),
            payload={"amount_minor": allocation.amount_minor, "currency": allocation.currency},
        )
    )
    await session.commit()
    await session.refresh(allocation)
    return allocation


@router.post(
    "/ops/payout-allocations/{allocation_id}/approve",
    response_model=PayoutAllocationView,
)
async def approve_payout_allocation(
    allocation_id: uuid.UUID,
    principal: Annotated[SessionPrincipal, Depends(require_roles(Role.PLATFORM_ADMIN))],
    session: DbSession,
    request: Request,
) -> PayoutAllocation:
    allocation = await session.get(PayoutAllocation, allocation_id, with_for_update=True)
    if allocation is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Payout allocation not found")
    if allocation.status != "PENDING":
        raise HTTPException(status.HTTP_409_CONFLICT, "Allocation is not pending")
    creator_id = await session.scalar(
        select(AuditEvent.actor_id).where(
            AuditEvent.resource_type == "payout_allocation",
            AuditEvent.resource_id == allocation.id,
            AuditEvent.action == "payout_allocation.created",
        )
    )
    if creator_id == principal.user_id:
        raise HTTPException(status.HTTP_409_CONFLICT, "Creator cannot approve the allocation")
    allocation.status = "APPROVED"
    allocation.approved_by_id = principal.user_id
    correlation_id = request.state.correlation_id
    session.add(
        AuditEvent(
            actor_id=principal.user_id,
            organization_id=principal.organization_id,
            action="payout_allocation.approved",
            resource_type="payout_allocation",
            resource_id=allocation.id,
            correlation_id=correlation_id,
            payload={"status": "APPROVED"},
        )
    )
    session.add(
        OutboxEvent(
            event_type="PayoutApproved",
            aggregate_type="payout_allocation",
            aggregate_id=allocation.id,
            payload={"allocation_id": str(allocation.id)},
        )
    )
    session.add(
        notification_event(
            recipient_user_id=allocation.recipient_user_id,
            category="payments",
            title="Payout approved",
            body=(
                "Your payout allocation was approved and is awaiting independently "
                "verified external payout evidence."
            ),
            resource_path="/student/earnings",
            correlation_id=correlation_id,
        )
    )
    await session.commit()
    await session.refresh(allocation)
    return allocation


@router.post(
    "/ops/payout-allocations/{allocation_id}/external-evidence",
    response_model=PayoutRecordView,
    status_code=201,
)
async def record_payout_evidence(
    allocation_id: uuid.UUID,
    body: ExternalPayoutRequest,
    principal: Annotated[SessionPrincipal, Depends(require_roles(Role.PLATFORM_ADMIN))],
    session: DbSession,
    idempotency_key: IdempotencyKey,
    request: Request,
) -> Payout:
    try:
        return await record_external_payout(
            session,
            allocation_id=allocation_id,
            body=body,
            principal=principal,
            idempotency_key=idempotency_key,
            correlation_id=request.state.correlation_id,
        )
    except PayoutNotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except PayoutError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
