import uuid

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.auth.service import SessionPrincipal
from app.billing.service import FundingError, record_manual_funding
from app.domain.enums import ProjectState
from app.domain.models import (
    AuditEvent,
    Base,
    LedgerEntry,
    Organization,
    OutboxEvent,
    PaymentEvent,
    Project,
    User,
)
from app.domain.schemas import ExternalFundingRequest


@pytest.mark.asyncio
async def test_manual_funding_is_hashed_balanced_and_idempotent() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    async with factory() as session:
        organization = Organization(name="Client", slug="funding-client", kind="client")
        coordinator = User(email="funding-ops@example.test", display_name="Coordinator")
        client = User(email="funding-client@example.test", display_name="Client")
        session.add_all([organization, coordinator, client])
        await session.flush()
        project = Project(
            client_organization_id=organization.id,
            created_by_id=client.id,
            title="Manual funding",
            description="A project funded outside PraxisAI with reviewed evidence.",
            category="dashboard",
            state=ProjectState.AWAITING_DEPOSIT.value,
            required_deposit_minor=50_000,
            funded_minor=0,
            currency="USD",
            is_demo=True,
        )
        session.add(project)
        await session.commit()
        principal = SessionPrincipal(coordinator.id, organization.id, "coordinator")
        evidence = ExternalFundingRequest(
            amount_minor=50_000,
            currency="USD",
            evidence_reference="bank-confirmation-demo-001",
            approved_arrangement=True,
        )

        first = await record_manual_funding(
            session,
            project_id=project.id,
            body=evidence,
            principal=principal,
            idempotency_key="manual-funding-once",
            correlation_id=uuid.uuid4(),
        )
        repeated = await record_manual_funding(
            session,
            project_id=project.id,
            body=evidence,
            principal=principal,
            idempotency_key="manual-funding-once",
            correlation_id=uuid.uuid4(),
        )

        assert first.id == repeated.id
        assert repeated.funded_minor == 50_000
        payment = await session.scalar(select(PaymentEvent))
        assert payment is not None
        assert payment.provider == "approved_external"
        assert payment.payload_hash != "not-provider-confirmed"
        assert await session.scalar(select(func.count(PaymentEvent.id))) == 1
        assert await session.scalar(select(func.sum(LedgerEntry.amount_minor))) == 0
        assert await session.scalar(select(func.count(LedgerEntry.id))) == 2
        assert await session.scalar(select(func.count(AuditEvent.id))) == 1
        assert (
            await session.scalar(
                select(func.count(OutboxEvent.id)).where(
                    OutboxEvent.event_type == "NotificationRequested"
                )
            )
            == 1
        )

        with pytest.raises(FundingError, match="different funding evidence"):
            await record_manual_funding(
                session,
                project_id=project.id,
                body=evidence.model_copy(update={"amount_minor": 60_000}),
                principal=principal,
                idempotency_key="manual-funding-once",
                correlation_id=uuid.uuid4(),
            )
    await engine.dispose()
