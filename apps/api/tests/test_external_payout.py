import uuid

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.auth.service import SessionPrincipal
from app.billing.service import PayoutError, record_external_payout
from app.domain.models import (
    AuditEvent,
    Base,
    LedgerEntry,
    Organization,
    OutboxEvent,
    Payout,
    PayoutAllocation,
    Project,
    User,
)
from app.domain.schemas import ExternalPayoutRequest


@pytest.mark.asyncio
async def test_external_payout_requires_separation_and_is_idempotent() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    async with factory() as session:
        organization = Organization(name="Operations", slug="payout-ops", kind="platform")
        client = User(email="payout-client@example.test", display_name="Client")
        recipient = User(email="payout-recipient@example.test", display_name="Recipient")
        approver = User(email="payout-approver@example.test", display_name="Approver")
        recorder = User(email="payout-recorder@example.test", display_name="Recorder")
        session.add_all([organization, client, recipient, approver, recorder])
        await session.flush()
        project = Project(
            client_organization_id=organization.id,
            created_by_id=client.id,
            title="Externally paid project",
            description="A project used to verify external payout evidence controls.",
            category="website",
            required_deposit_minor=100_000,
            funded_minor=100_000,
        )
        session.add(project)
        await session.flush()
        allocation = PayoutAllocation(
            project_id=project.id,
            recipient_user_id=recipient.id,
            amount_minor=80_000,
            currency="USD",
            status="APPROVED",
            approved_by_id=approver.id,
        )
        session.add(allocation)
        await session.commit()
        body = ExternalPayoutRequest(
            approved_arrangement=True,
            external_reference="external-bank-reference-001",
            evidence_summary="Operator verified the approved external bank payout record.",
        )
        recorder_principal = SessionPrincipal(recorder.id, organization.id, "platform_admin")

        with pytest.raises(PayoutError, match="Approver cannot"):
            await record_external_payout(
                session,
                allocation_id=allocation.id,
                body=body,
                principal=SessionPrincipal(approver.id, organization.id, "platform_admin"),
                idempotency_key="approver-cannot-record",
                correlation_id=uuid.uuid4(),
            )

        payout = await record_external_payout(
            session,
            allocation_id=allocation.id,
            body=body,
            principal=recorder_principal,
            idempotency_key="external-payout-once",
            correlation_id=uuid.uuid4(),
        )
        replay = await record_external_payout(
            session,
            allocation_id=allocation.id,
            body=body,
            principal=recorder_principal,
            idempotency_key="external-payout-once",
            correlation_id=uuid.uuid4(),
        )

        assert payout.id == replay.id
        assert payout.status == "RECORDED_EXTERNALLY"
        assert payout.evidence_hash is not None and len(payout.evidence_hash) == 64
        assert (await session.get(PayoutAllocation, allocation.id)).status == "PAID"
        assert await session.scalar(select(func.count()).select_from(Payout)) == 1
        assert await session.scalar(select(func.count()).select_from(AuditEvent)) == 1
        assert await session.scalar(select(func.count()).select_from(OutboxEvent)) == 1
        ledger_total = await session.scalar(select(func.sum(LedgerEntry.amount_minor)))
        assert ledger_total == 0
        with pytest.raises(PayoutError, match="different payout"):
            await record_external_payout(
                session,
                allocation_id=allocation.id,
                body=ExternalPayoutRequest(
                    approved_arrangement=True,
                    external_reference="changed-external-reference",
                    evidence_summary=(
                        "This changed payload must not replay under the original key."
                    ),
                ),
                principal=recorder_principal,
                idempotency_key="external-payout-once",
                correlation_id=uuid.uuid4(),
            )

        second_allocation = PayoutAllocation(
            project_id=project.id,
            recipient_user_id=recipient.id,
            amount_minor=10_000,
            currency="USD",
            status="APPROVED",
            approved_by_id=approver.id,
        )
        session.add(second_allocation)
        await session.commit()
        with pytest.raises(PayoutError, match="different payout"):
            await record_external_payout(
                session,
                allocation_id=second_allocation.id,
                body=body,
                principal=recorder_principal,
                idempotency_key="external-payout-once",
                correlation_id=uuid.uuid4(),
            )
    await engine.dispose()
