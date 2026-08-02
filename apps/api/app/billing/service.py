import hashlib
import json
import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.service import SessionPrincipal
from app.domain.enums import ProjectState, Role
from app.domain.models import (
    AuditEvent,
    LedgerEntry,
    PaymentEvent,
    Payout,
    PayoutAllocation,
    Project,
)
from app.domain.schemas import ExternalFundingRequest, ExternalPayoutRequest
from app.notifications.service import notification_event


class LedgerError(ValueError):
    pass


class FundingError(ValueError):
    pass


class FundingNotFound(FundingError):
    pass


class PayoutError(ValueError):
    pass


class PayoutNotFound(PayoutError):
    pass


def _external_payout_snapshot(
    allocation: PayoutAllocation, body: ExternalPayoutRequest
) -> dict[str, object]:
    return {
        "allocation_id": str(allocation.id),
        "project_id": str(allocation.project_id),
        "recipient_user_id": str(allocation.recipient_user_id),
        "amount_minor": allocation.amount_minor,
        "currency": allocation.currency,
        "approved_arrangement": body.approved_arrangement,
        "external_reference": body.external_reference,
        "evidence_summary": body.evidence_summary,
    }


def _snapshot_hash(snapshot: dict[str, object]) -> str:
    return hashlib.sha256(
        json.dumps(snapshot, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


async def post_balanced_transaction(
    session: AsyncSession,
    *,
    project_id: uuid.UUID,
    currency: str,
    entries: dict[str, int],
    memo: str,
) -> uuid.UUID:
    if len(entries) < 2 or sum(entries.values()) != 0:
        raise LedgerError("Ledger transaction must contain balanced debit and credit entries")
    if any(amount == 0 for amount in entries.values()):
        raise LedgerError("Zero-value ledger entries are not permitted")
    transaction_id = uuid.uuid4()
    for account, amount in entries.items():
        session.add(
            LedgerEntry(
                transaction_id=transaction_id,
                project_id=project_id,
                account=account,
                amount_minor=amount,
                currency=currency,
                memo=memo,
            )
        )
    return transaction_id


async def assert_transaction_balanced(session: AsyncSession, transaction_id: uuid.UUID) -> None:
    total = await session.scalar(
        select(func.coalesce(func.sum(LedgerEntry.amount_minor), 0)).where(
            LedgerEntry.transaction_id == transaction_id
        )
    )
    if total != 0:
        raise LedgerError("Stored ledger transaction is unbalanced")


async def record_manual_funding(
    session: AsyncSession,
    *,
    project_id: uuid.UUID,
    body: ExternalFundingRequest,
    principal: SessionPrincipal,
    idempotency_key: str,
    correlation_id: uuid.UUID,
) -> Project:
    if principal.role != Role.COORDINATOR.value:
        raise FundingError("Coordinator role is required")
    if not body.approved_arrangement:
        raise FundingError("Approval must be explicit")
    snapshot = {
        "project_id": str(project_id),
        "amount_minor": body.amount_minor,
        "currency": body.currency,
        "evidence_reference": body.evidence_reference,
        "approved_arrangement": body.approved_arrangement,
    }
    payload_hash = hashlib.sha256(
        json.dumps(snapshot, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    key_hash = hashlib.sha256(idempotency_key.encode()).hexdigest()
    provider_event_id = f"manual-{key_hash}"
    existing = await session.scalar(
        select(PaymentEvent).where(PaymentEvent.provider_event_id == provider_event_id)
    )
    if existing is not None:
        if existing.project_id != project_id or existing.payload_hash != payload_hash:
            raise FundingError("Idempotency key belongs to different funding evidence")
        project: Project | None = await session.scalar(
            select(Project).where(Project.id == project_id)
        )
        if project is None:
            raise FundingNotFound("Project not found")
        return project

    project = await session.scalar(
        select(Project).where(Project.id == project_id).with_for_update()
    )
    if project is None:
        raise FundingNotFound("Project not found")
    if project.state != ProjectState.AWAITING_DEPOSIT.value:
        raise FundingError("External funding evidence can only be recorded while awaiting deposit")
    if body.currency != project.currency:
        raise FundingError("Funding currency mismatch")

    now = datetime.now(UTC)
    project.funded_minor += body.amount_minor
    session.add(
        PaymentEvent(
            provider="approved_external",
            provider_event_id=provider_event_id,
            project_id=project.id,
            event_type="funding.evidence_recorded",
            environment="demo" if project.is_demo else "manual",
            payload_hash=payload_hash,
            processed_at=now,
        )
    )
    session.add(
        AuditEvent(
            actor_id=principal.user_id,
            organization_id=principal.organization_id,
            action="funding.external_recorded",
            resource_type="project",
            resource_id=project.id,
            correlation_id=correlation_id,
            payload={**snapshot, "source": "approved_external_manual"},
        )
    )
    await post_balanced_transaction(
        session,
        project_id=project.id,
        currency=project.currency,
        entries={
            "external_funding_evidence": body.amount_minor,
            "client_funding_liability": -body.amount_minor,
        },
        memo=provider_event_id,
    )
    session.add(
        notification_event(
            recipient_user_id=project.created_by_id,
            category="payments",
            title="External funding evidence recorded",
            body=(
                "An operator recorded approved external funding evidence. "
                "PraxisAI did not process the payment."
            ),
            resource_path=f"/client/projects/{project.id}",
            correlation_id=correlation_id,
        )
    )
    await session.commit()
    await session.refresh(project)
    return project


async def record_external_payout(
    session: AsyncSession,
    *,
    allocation_id: uuid.UUID,
    body: ExternalPayoutRequest,
    principal: SessionPrincipal,
    idempotency_key: str,
    correlation_id: uuid.UUID,
) -> Payout:
    if principal.role != Role.PLATFORM_ADMIN.value:
        raise PayoutError("Platform administrator role is required")
    replay = await session.scalar(select(Payout).where(Payout.idempotency_key == idempotency_key))
    if replay is not None:
        if replay.allocation_id != allocation_id:
            raise PayoutError("Idempotency key belongs to different payout evidence")
        replay_allocation = await session.get(PayoutAllocation, replay.allocation_id)
        if replay_allocation is None:
            raise PayoutNotFound("Payout allocation not found")
        if replay.evidence_hash != _snapshot_hash(
            _external_payout_snapshot(replay_allocation, body)
        ):
            raise PayoutError("Idempotency key belongs to different payout evidence")
        return replay
    allocation = await session.scalar(
        select(PayoutAllocation).where(PayoutAllocation.id == allocation_id).with_for_update()
    )
    if allocation is None:
        raise PayoutNotFound("Payout allocation not found")
    if allocation.status != "APPROVED":
        raise PayoutError("Allocation is not approved")
    if allocation.approved_by_id == principal.user_id:
        raise PayoutError("Approver cannot record external payout evidence")
    reference_in_use = await session.scalar(
        select(Payout.id).where(Payout.provider_reference == body.external_reference)
    )
    if reference_in_use is not None:
        raise PayoutError("External payout reference was already recorded")
    snapshot = _external_payout_snapshot(allocation, body)
    evidence_hash = _snapshot_hash(snapshot)
    payout = Payout(
        allocation_id=allocation.id,
        provider_reference=body.external_reference,
        status="RECORDED_EXTERNALLY",
        failure_reason=None,
        evidence_hash=evidence_hash,
        idempotency_key=idempotency_key,
    )
    allocation.status = "PAID"
    session.add(payout)
    await session.flush()
    await post_balanced_transaction(
        session,
        project_id=allocation.project_id,
        currency=allocation.currency,
        entries={
            "client_funding_liability": allocation.amount_minor,
            "external_payout_evidence": -allocation.amount_minor,
        },
        memo=f"external-payout:{payout.id}",
    )
    session.add(
        AuditEvent(
            actor_id=principal.user_id,
            organization_id=principal.organization_id,
            action="payout.external_evidence_recorded",
            resource_type="payout",
            resource_id=payout.id,
            correlation_id=correlation_id,
            payload={**snapshot, "evidence_hash": evidence_hash},
        )
    )
    session.add(
        notification_event(
            recipient_user_id=allocation.recipient_user_id,
            category="payments",
            title="External payout evidence recorded",
            body=(
                "An operator recorded evidence of an approved external payout. "
                "PraxisAI did not execute the payment."
            ),
            resource_path="/student/earnings",
            correlation_id=correlation_id,
        )
    )
    await session.commit()
    await session.refresh(payout)
    return payout
