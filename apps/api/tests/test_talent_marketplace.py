import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.auth.service import SessionPrincipal
from app.domain.models import (
    AuditEvent,
    Base,
    Organization,
    Project,
    ProjectOpportunity,
    StudentProfile,
    StudentProposal,
    User,
)
from app.domain.schemas import (
    OpportunityPublishRequest,
    ProposalDecisionRequest,
    ProposalEvidence,
    ProposalPlanStep,
    StudentProposalCreate,
)
from app.talent.service import (
    TalentError,
    TalentNotFound,
    decide_proposal,
    publish_opportunity,
    submit_proposal,
)


def proposal_body(*, amount_minor: int = 90_000, availability: int = 10) -> StudentProposalCreate:
    return StudentProposalCreate(
        cover_note=(
            "I have delivered comparable accessible workflows and can connect the business brief "
            "to tested user outcomes."
        ),
        approach=(
            "I will clarify the acceptance criteria, build the smallest complete workflow, run "
            "automated and keyboard checks, and submit milestone evidence for employer review."
        ),
        delivery_plan=[
            ProposalPlanStep(
                milestone="Validated workflow",
                outcome=(
                    "A reviewed implementation with test evidence against every acceptance "
                    "criterion."
                ),
            )
        ],
        relevant_evidence=[
            ProposalEvidence(
                title="Accessible workflow sample",
                url="https://example.test/evidence",
                relevance=(
                    "Shows comparable requirements analysis, implementation, and verification "
                    "evidence."
                ),
            )
        ],
        proposed_amount_minor=amount_minor,
        currency="USD",
        estimated_days=10,
        availability_hours_per_week=availability,
    )


@pytest.mark.asyncio
async def test_employer_selects_one_idempotent_student_proposal() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    employer_org_id = uuid.uuid4()
    other_org_id = uuid.uuid4()
    employer_id = uuid.uuid4()
    first_student_id = uuid.uuid4()
    second_student_id = uuid.uuid4()
    async with factory() as session:
        session: AsyncSession
        session.add_all(
            [
                Organization(
                    id=employer_org_id,
                    name="Employer Test Organization",
                    slug="employer-test",
                    kind="client",
                ),
                Organization(
                    id=other_org_id,
                    name="Other Organization",
                    slug="other-employer-test",
                    kind="client",
                ),
                User(
                    id=employer_id,
                    email="employer@example.test",
                    display_name="Employer Owner",
                    external_subject="employer-owner",
                ),
                User(
                    id=first_student_id,
                    email="first@example.test",
                    display_name="First Student",
                    external_subject="first-student",
                ),
                User(
                    id=second_student_id,
                    email="second@example.test",
                    display_name="Second Student",
                    external_subject="second-student",
                ),
                StudentProfile(
                    user_id=first_student_id,
                    confirmed_18_plus=True,
                    eligible=True,
                    workload_cap_hours=20,
                ),
                StudentProfile(
                    user_id=second_student_id,
                    confirmed_18_plus=True,
                    eligible=True,
                    workload_cap_hours=20,
                ),
            ]
        )
        project = Project(
            client_organization_id=employer_org_id,
            created_by_id=employer_id,
            title="Accessible service directory",
            description="Create a tested resource discovery workflow for community users.",
            category="website",
            currency="USD",
        )
        session.add(project)
        await session.commit()

        employer = SessionPrincipal(employer_id, employer_org_id, "client_owner")
        published = await publish_opportunity(
            session,
            body=OpportunityPublishRequest(
                project_id=project.id,
                headline="Build an accessible service directory",
                brief=(
                    "Community members need to find verified services by location and category. "
                    "The result must be keyboard accessible, responsive, and backed by meaningful "
                    "tests."
                ),
                required_skills=["TypeScript", "Accessibility"],
                nice_to_have_skills=["User research"],
                deliverables=["Responsive directory", "Verification report"],
                proposal_requirements=["Explain delivery approach", "Link relevant evidence"],
                estimated_hours_low=24,
                estimated_hours_high=36,
                budget_minor=120_000,
                currency="USD",
                deadline=datetime.now(UTC) + timedelta(days=30),
                supervision_level="guided",
                max_proposals=10,
            ),
            principal=employer,
            correlation_id=uuid.uuid4(),
        )

        first_key = str(uuid.uuid4())
        first = await submit_proposal(
            session,
            opportunity_id=published.id,
            body=proposal_body(),
            principal=SessionPrincipal(first_student_id, employer_org_id, "student"),
            idempotency_key=first_key,
            correlation_id=uuid.uuid4(),
        )
        replay = await submit_proposal(
            session,
            opportunity_id=published.id,
            body=proposal_body(),
            principal=SessionPrincipal(first_student_id, employer_org_id, "student"),
            idempotency_key=first_key,
            correlation_id=uuid.uuid4(),
        )
        assert replay.id == first.id
        with pytest.raises(TalentNotFound, match="Proposal not found"):
            await submit_proposal(
                session,
                opportunity_id=published.id,
                body=proposal_body(),
                principal=SessionPrincipal(second_student_id, employer_org_id, "student"),
                idempotency_key=first_key,
                correlation_id=uuid.uuid4(),
            )

        second = await submit_proposal(
            session,
            opportunity_id=published.id,
            body=proposal_body(amount_minor=110_000),
            principal=SessionPrincipal(second_student_id, employer_org_id, "student"),
            idempotency_key=str(uuid.uuid4()),
            correlation_id=uuid.uuid4(),
        )

        with pytest.raises(TalentNotFound, match="Proposal not found"):
            await decide_proposal(
                session,
                proposal_id=first.id,
                body=ProposalDecisionRequest(
                    decision="ACCEPTED",
                    reason="The evidence and delivery plan best match the published requirements.",
                ),
                principal=SessionPrincipal(employer_id, other_org_id, "client_owner"),
                idempotency_key=str(uuid.uuid4()),
                correlation_id=uuid.uuid4(),
            )

        decision_key = str(uuid.uuid4())
        accepted = await decide_proposal(
            session,
            proposal_id=first.id,
            body=ProposalDecisionRequest(
                decision="ACCEPTED",
                reason="The evidence and delivery plan best match the published requirements.",
            ),
            principal=employer,
            idempotency_key=decision_key,
            correlation_id=uuid.uuid4(),
        )
        decision_replay = await decide_proposal(
            session,
            proposal_id=first.id,
            body=ProposalDecisionRequest(
                decision="ACCEPTED",
                reason="The evidence and delivery plan best match the published requirements.",
            ),
            principal=employer,
            idempotency_key=decision_key,
            correlation_id=uuid.uuid4(),
        )
        with pytest.raises(TalentNotFound, match="Proposal not found"):
            await decide_proposal(
                session,
                proposal_id=first.id,
                body=ProposalDecisionRequest(
                    decision="ACCEPTED",
                    reason="The evidence and delivery plan best match the published requirements.",
                ),
                principal=SessionPrincipal(employer_id, other_org_id, "client_owner"),
                idempotency_key=decision_key,
                correlation_id=uuid.uuid4(),
            )
        assert accepted.state == "ACCEPTED"
        assert decision_replay.id == accepted.id
        opportunity = await session.get(ProjectOpportunity, published.id)
        competing = await session.get(StudentProposal, second.id)
        assert opportunity is not None and opportunity.status == "SELECTED"
        assert competing is not None and competing.state == "REJECTED"
        assert "no reputation" not in (competing.decision_reason or "").lower()
        audit_actions = set((await session.scalars(select(AuditEvent.action))).all())
        assert {"opportunity.published", "proposal.submitted", "proposal.decided"} <= audit_actions

    await engine.dispose()


@pytest.mark.asyncio
async def test_proposal_cannot_exceed_budget_or_available_workload() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    organization_id = uuid.uuid4()
    employer_id = uuid.uuid4()
    student_id = uuid.uuid4()
    async with factory() as session:
        session.add_all(
            [
                Organization(
                    id=organization_id,
                    name="Budget Test Employer",
                    slug="budget-test-employer",
                    kind="client",
                ),
                User(
                    id=employer_id,
                    email="budget-employer@example.test",
                    display_name="Budget Employer",
                    external_subject="budget-employer",
                ),
                User(
                    id=student_id,
                    email="capacity@example.test",
                    display_name="Capacity Student",
                    external_subject="capacity-student",
                ),
                StudentProfile(
                    user_id=student_id,
                    confirmed_18_plus=True,
                    eligible=True,
                    workload_cap_hours=12,
                    committed_hours=8,
                ),
            ]
        )
        project = Project(
            client_organization_id=organization_id,
            created_by_id=employer_id,
            title="Budget boundary project",
            description="Verify proposal commercial and workload boundaries.",
            category="website",
            currency="USD",
        )
        session.add(project)
        await session.flush()
        opportunity = ProjectOpportunity(
            project_id=project.id,
            published_by_id=employer_id,
            headline="Boundary-tested paid opportunity",
            brief="A complete project brief that is long enough for the persistence boundary test.",
            required_skills=["Testing"],
            nice_to_have_skills=[],
            deliverables=["Verified implementation"],
            proposal_requirements=["Evidence"],
            estimated_hours_low=8,
            estimated_hours_high=12,
            budget_minor=100_000,
            currency="USD",
            deadline=datetime.now(UTC) + timedelta(days=14),
            supervision_level="guided",
            status="OPEN",
        )
        session.add(opportunity)
        await session.commit()
        principal = SessionPrincipal(student_id, organization_id, "student")

        with pytest.raises(TalentError, match="budget"):
            await submit_proposal(
                session,
                opportunity_id=opportunity.id,
                body=proposal_body(amount_minor=100_001, availability=4),
                principal=principal,
                idempotency_key=str(uuid.uuid4()),
                correlation_id=uuid.uuid4(),
            )

        with pytest.raises(TalentError, match="workload"):
            await submit_proposal(
                session,
                opportunity_id=opportunity.id,
                body=proposal_body(amount_minor=90_000, availability=5),
                principal=principal,
                idempotency_key=str(uuid.uuid4()),
                correlation_id=uuid.uuid4(),
            )

    await engine.dispose()
