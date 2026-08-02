import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.auth.service import SessionPrincipal
from app.domain.models import (
    AssignmentOffer,
    Base,
    Organization,
    OutboxEvent,
    Project,
    ProjectAssignment,
    ReputationEvent,
    StudentProfile,
    User,
)
from app.offers.service import OfferError, decide_offer


@pytest.mark.asyncio
async def test_offer_acceptance_is_idempotent_and_creates_one_assignment() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    async with factory() as session:
        organization = Organization(name="Demo", slug="offer-demo", kind="platform")
        client = User(email="offer-client@example.test", display_name="Client")
        student = User(email="offer-student@example.test", display_name="Student")
        session.add_all([organization, client, student])
        await session.flush()
        session.add(
            StudentProfile(
                user_id=student.id,
                bio="Eligible student",
                timezone="UTC",
                eligible=True,
                confirmed_18_plus=True,
                workload_cap_hours=20,
                committed_hours=2,
                completed_projects=0,
            )
        )
        project = Project(
            client_organization_id=organization.id,
            created_by_id=client.id,
            title="Idempotent offer project",
            description="A sufficiently detailed project used to test offer decisions.",
            category="website",
            required_deposit_minor=100_000,
            funded_minor=100_000,
        )
        session.add(project)
        await session.flush()
        offer = AssignmentOffer(
            project_id=project.id,
            recipient_user_id=student.id,
            role="student developer",
            state="OFFERED",
            terms_snapshot={"expected_weekly_hours": 8},
            expires_at=datetime.now(UTC) + timedelta(days=1),
        )
        session.add(offer)
        await session.commit()
        principal = SessionPrincipal(student.id, organization.id, "student")
        correlation_id = uuid.uuid4()

        first = await decide_offer(
            session,
            offer_id=offer.id,
            principal=principal,
            accept=True,
            correlation_id=correlation_id,
            idempotency_key="accept-offer-once",
        )
        replay = await decide_offer(
            session,
            offer_id=offer.id,
            principal=principal,
            accept=True,
            correlation_id=correlation_id,
            idempotency_key="accept-offer-once",
        )

        assert first.id == replay.id
        assert first.state == "ACCEPTED"
        assert await session.scalar(select(func.count()).select_from(ProjectAssignment)) == 1
        assert await session.scalar(select(func.count()).select_from(OutboxEvent)) == 2
        with pytest.raises(OfferError, match="another decision"):
            await decide_offer(
                session,
                offer_id=offer.id,
                principal=principal,
                accept=False,
                correlation_id=correlation_id,
                idempotency_key="accept-offer-once",
            )
        assert await session.scalar(select(func.count()).select_from(ReputationEvent)) == 0
    await engine.dispose()
