import asyncio
import sys
import uuid
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "apps" / "api"))

from app.auth.service import SessionPrincipal
from app.billing.service import record_external_payout
from app.config import get_settings
from app.credentials.service import DemoSigningProvider, build_signed_credential
from app.db import SessionFactory
from app.domain.enums import OfferState, ProjectState, Role
from app.domain.models import (
    Approval,
    AssignmentOffer,
    AvailabilityWindow,
    ClientDecision,
    ConsentRecord,
    Credential,
    CredentialEvidence,
    Deliverable,
    DeliverableArtifact,
    InstitutionalAgreement,
    Invoice,
    LeadProfile,
    LeadReview,
    LearningEnrollment,
    LearningModule,
    LearningModuleCompletion,
    LearningPath,
    Milestone,
    Organization,
    OrganizationMembership,
    OutboxEvent,
    PayoutAllocation,
    PolicyVersion,
    PortfolioPermission,
    Project,
    ProjectOpportunity,
    ProjectAssignment,
    ProjectRisk,
    ProjectTransition,
    QAReview,
    Skill,
    StudentProfile,
    StudentProposal,
    StudentSkill,
    Task,
    University,
    UniversityEnrollment,
    User,
    WorkLog,
)
from app.domain.schemas import ExternalPayoutRequest
from app.notifications.service import notification_event
from seed_internships import seed_internship_demo

NAMESPACE = uuid.UUID("d852f362-f05c-4eb4-899a-24e0b4d96660")


def identifier(name: str) -> uuid.UUID:
    return uuid.uuid5(NAMESPACE, name)


async def upsert(session, model, seed_key: str, **values):
    item_id = identifier(seed_key)
    existing = await session.get(model, item_id)
    if existing is not None:
        for key, value in values.items():
            setattr(existing, key, value)
        return existing
    item = model(id=item_id, **values)
    session.add(item)
    await session.flush()
    return item


async def insert_immutable(session, model, seed_key: str, **values):
    item_id = identifier(seed_key)
    existing = await session.get(model, item_id)
    if existing is not None:
        return existing
    item = model(id=item_id, **values)
    session.add(item)
    await session.flush()
    return item


async def seed() -> None:
    settings = get_settings()
    if not (settings.is_local_or_test or settings.demo_mode):
        raise RuntimeError("Demo seed is refused outside local/test/demo")
    async with SessionFactory() as session:
        client_org = await upsert(
            session,
            Organization,
            "org-client",
            name="Northstar Civic Studio (Fictional)",
            slug="northstar-demo",
            kind="client",
            is_demo=True,
        )
        ops_org = await upsert(
            session,
            Organization,
            "org-ops",
            name="PraxisAI Pilot Operations",
            slug="praxis-ops-demo",
            kind="platform",
            is_demo=True,
        )
        uni_org = await upsert(
            session,
            Organization,
            "org-uni",
            name="Westbridge University (Fictional)",
            slug="westbridge-demo",
            kind="university",
            is_demo=True,
        )

        users = {
            "client": await upsert(
                session,
                User,
                "user-client",
                email="maya@northstar.demo",
                display_name="Maya Chen",
                external_subject=None,
                is_active=True,
                is_demo=True,
            ),
            "student": await upsert(
                session,
                User,
                "user-student",
                email="amina@student.demo",
                display_name="Amina Noor",
                external_subject=None,
                is_active=True,
                is_demo=True,
            ),
            "available": await upsert(
                session,
                User,
                "user-available",
                email="leo@student.demo",
                display_name="Leo Martins",
                external_subject=None,
                is_active=True,
                is_demo=True,
            ),
            "unavailable": await upsert(
                session,
                User,
                "user-unavailable",
                email="rhea@student.demo",
                display_name="Rhea Kapoor",
                external_subject=None,
                is_active=True,
                is_demo=True,
            ),
            "partial": await upsert(
                session,
                User,
                "user-partial",
                email="jon@student.demo",
                display_name="Jon Bell",
                external_subject=None,
                is_active=True,
                is_demo=True,
            ),
            "overloaded": await upsert(
                session,
                User,
                "user-overloaded",
                email="sam@student.demo",
                display_name="Sam Ortiz",
                external_subject=None,
                is_active=True,
                is_demo=True,
            ),
            "suspended": await upsert(
                session,
                User,
                "user-suspended",
                email="nia@student.demo",
                display_name="Nia Brooks",
                external_subject=None,
                is_active=True,
                is_demo=True,
            ),
            "lead": await upsert(
                session,
                User,
                "user-lead",
                email="david@lead.demo",
                display_name="David Okafor",
                external_subject=None,
                is_active=True,
                is_demo=True,
            ),
            "lead_conflict": await upsert(
                session,
                User,
                "user-lead-conflict",
                email="elena@lead.demo",
                display_name="Elena Rossi",
                external_subject=None,
                is_active=True,
                is_demo=True,
            ),
            "coordinator": await upsert(
                session,
                User,
                "user-coordinator",
                email="sara@praxis.demo",
                display_name="Sara Malik",
                external_subject=None,
                is_active=True,
                is_demo=True,
            ),
            "admin": await upsert(
                session,
                User,
                "user-admin",
                email="admin@praxis.demo",
                display_name="Platform Operator",
                external_subject=None,
                is_active=True,
                is_demo=True,
            ),
            "university": await upsert(
                session,
                User,
                "user-university",
                email="viewer@westbridge.demo",
                display_name="Dr. Ellis Grant",
                external_subject=None,
                is_active=True,
                is_demo=True,
            ),
        }

        memberships = [
            ("client", client_org, Role.CLIENT_OWNER),
            ("student", ops_org, Role.STUDENT),
            ("available", ops_org, Role.STUDENT),
            ("unavailable", ops_org, Role.STUDENT),
            ("partial", ops_org, Role.STUDENT),
            ("overloaded", ops_org, Role.STUDENT),
            ("suspended", ops_org, Role.STUDENT),
            ("lead", ops_org, Role.TECHNICAL_LEAD),
            ("lead_conflict", ops_org, Role.TECHNICAL_LEAD),
            ("coordinator", ops_org, Role.COORDINATOR),
            ("admin", ops_org, Role.PLATFORM_ADMIN),
            ("university", uni_org, Role.UNIVERSITY_VIEWER),
        ]
        for key, org, role in memberships:
            await upsert(
                session,
                OrganizationMembership,
                f"membership-{key}",
                user_id=users[key].id,
                organization_id=org.id,
                role=role.value,
                is_active=True,
            )

        student_specs = {
            "student": (True, 20, 8, 0),
            "available": (True, 24, 4, 2),
            "unavailable": (True, 0, 0, 1),
            "partial": (True, 15, 2, 0),
            "overloaded": (True, 10, 10, 3),
            "suspended": (False, 20, 0, 1),
        }
        profiles = {}
        for key, (eligible, cap, committed, completed) in student_specs.items():
            profiles[key] = await upsert(
                session,
                StudentProfile,
                f"profile-{key}",
                user_id=users[key].id,
                bio="Fictional demo profile",
                timezone="UTC",
                eligible=eligible,
                confirmed_18_plus=True,
                workload_cap_hours=cap,
                committed_hours=committed,
                completed_projects=completed,
            )
            await upsert(
                session,
                AvailabilityWindow,
                f"availability-{key}",
                student_profile_id=profiles[key].id,
                starts_on=date.today(),
                ends_on=date.today() + timedelta(days=60),
                hours_per_week=max(0, cap - committed),
            )

        university = await upsert(
            session,
            University,
            "university-westbridge",
            organization_id=uni_org.id,
            agreement_status="ACTIVE",
        )
        await upsert(
            session,
            InstitutionalAgreement,
            "agreement-westbridge-v1",
            university_id=university.id,
            version=1,
            status="ACTIVE",
            entitlements=["aggregate_metrics", "exports"],
            starts_at=datetime.now(UTC) - timedelta(days=30),
            ends_at=datetime.now(UTC) + timedelta(days=335),
        )
        for key in ["student", "available", "partial", "overloaded", "suspended"]:
            await upsert(
                session,
                UniversityEnrollment,
                f"university-enrollment-{key}",
                university_id=university.id,
                student_profile_id=profiles[key].id,
                consented=True,
            )
        await upsert(
            session,
            UniversityEnrollment,
            "university-enrollment-unavailable",
            university_id=university.id,
            student_profile_id=profiles["unavailable"].id,
            consented=False,
        )

        web_skill = await upsert(
            session, Skill, "skill-web", name="TypeScript web development"
        )
        testing_skill = await upsert(
            session, Skill, "skill-testing", name="Software testing"
        )
        for key, proficiency, evidence in [
            ("student", 4, 2),
            ("available", 5, 4),
            ("unavailable", 4, 3),
            ("partial", 2, 0),
            ("overloaded", 5, 5),
            ("suspended", 4, 2),
        ]:
            await upsert(
                session,
                StudentSkill,
                f"student-skill-{key}-web",
                student_profile_id=profiles[key].id,
                skill_id=web_skill.id,
                proficiency=proficiency,
                source="verified" if evidence else "self_declared",
                evidence_count=evidence,
            )
            if key in {"student", "available", "overloaded"}:
                await upsert(
                    session,
                    StudentSkill,
                    f"student-skill-{key}-test",
                    student_profile_id=profiles[key].id,
                    skill_id=testing_skill.id,
                    proficiency=max(3, proficiency - 1),
                    source="verified",
                    evidence_count=max(1, evidence - 1),
                )

        await upsert(
            session,
            LeadProfile,
            "lead-profile",
            user_id=users["lead"].id,
            domains=["web", "accessibility"],
            verified=True,
            workload_cap_hours=12,
            committed_hours=3,
        )
        await upsert(
            session,
            LeadProfile,
            "lead-conflict-profile",
            user_id=users["lead_conflict"].id,
            domains=["web"],
            verified=True,
            workload_cap_hours=10,
            committed_hours=1,
        )
        await upsert(
            session,
            PolicyVersion,
            "policy-pilot",
            policy_name="pilot",
            version=1,
            payload={
                "currency": "USD",
                "effort_cap_hours": 40,
                "revision_rounds": 2,
                "offer_expiry_hours": 72,
                "matching_weights": {
                    "skill_fit": 40,
                    "verified_evidence": 20,
                    "availability": 15,
                    "reliability": 15,
                    "complexity_readiness": 10,
                },
            },
            active_from=datetime.now(UTC),
            is_demo=True,
        )

        frontend_path = await upsert(
            session,
            LearningPath,
            "learning-path-frontend-delivery",
            slug="frontend-delivery-foundations",
            title="Frontend delivery foundations",
            summary=(
                "Learn how a professional team turns an approved brief into an accessible, "
                "tested interface with reviewable evidence."
            ),
            level="FOUNDATION",
            estimated_hours=12,
            skill_outcomes=[
                "Translate acceptance criteria into interface behavior",
                "Build responsive TypeScript components",
                "Test keyboard and screen-reader workflows",
                "Prepare evidence for technical review",
            ],
            prerequisites=["Basic HTML and CSS", "Introductory JavaScript"],
            active=True,
            is_demo=True,
        )
        frontend_modules = [
            await upsert(
                session,
                LearningModule,
                "learning-module-brief-to-criteria",
                learning_path_id=frontend_path.id,
                ordinal=1,
                title="From business brief to acceptance criteria",
                summary="Turn ambiguous requests into observable user outcomes and boundaries.",
                estimated_minutes=90,
                content_sections=[
                    {
                        "title": "Read for outcomes",
                        "body": (
                            "Separate the employer's desired result from requested features. "
                            "Record users, constraints, dependencies, and measurable success."
                        ),
                    },
                    {
                        "title": "Write testable criteria",
                        "body": (
                            "Each criterion should describe an observable behavior, its context, "
                            "and the evidence that will demonstrate completion."
                        ),
                    },
                ],
                exercise_brief=(
                    "Rewrite a vague dashboard request into five testable acceptance criteria, "
                    "two explicit exclusions, and three clarification questions."
                ),
                completion_evidence="A concise criteria set with rationale for every boundary.",
            ),
            await upsert(
                session,
                LearningModule,
                "learning-module-accessible-components",
                learning_path_id=frontend_path.id,
                ordinal=2,
                title="Accessible component implementation",
                summary="Build semantic, keyboard-operable components with useful states.",
                estimated_minutes=180,
                content_sections=[
                    {
                        "title": "Semantic structure first",
                        "body": (
                            "Use native controls and landmarks before adding ARIA. Preserve label, "
                            "error, focus, loading, empty, and denial states."
                        ),
                    },
                    {
                        "title": "Responsive interaction",
                        "body": (
                            "Validate behavior at narrow widths and with keyboard-only navigation; "
                            "do not hide essential decisions on mobile."
                        ),
                    },
                ],
                exercise_brief=(
                    "Implement a project card and proposal form that remain usable with keyboard, "
                    "screen reader, reduced motion, and a 360px viewport."
                ),
                completion_evidence="Repository or sandbox URL plus keyboard test observations.",
            ),
            await upsert(
                session,
                LearningModule,
                "learning-module-delivery-evidence",
                learning_path_id=frontend_path.id,
                ordinal=3,
                title="Testing and delivery evidence",
                summary="Prove completion with focused automated and human review evidence.",
                estimated_minutes=150,
                content_sections=[
                    {
                        "title": "Test the contract",
                        "body": (
                            "Map tests to acceptance criteria. A passing test is useful only when "
                            "its assertion would fail for the behavior it claims to protect."
                        ),
                    },
                    {
                        "title": "Prepare review evidence",
                        "body": (
                            "Bind screenshots, test output, commit identifiers, and known limits to "
                            "the exact artifact version being reviewed."
                        ),
                    },
                ],
                exercise_brief=(
                    "Create a release evidence note mapping three criteria to tests, manual checks, "
                    "and immutable artifact references."
                ),
                completion_evidence="Evidence matrix with criterion, method, result, and artifact reference.",
            ),
        ]
        data_path = await upsert(
            session,
            LearningPath,
            "learning-path-data-storytelling",
            slug="data-quality-and-storytelling",
            title="Data quality and decision storytelling",
            summary=(
                "Learn to inspect messy operational data, define trustworthy metrics, and present "
                "a decision-ready dashboard without overstating evidence."
            ),
            level="INTERMEDIATE",
            estimated_hours=15,
            skill_outcomes=[
                "Profile and validate source data",
                "Define metrics with explicit denominators",
                "Build decision-focused dashboards",
                "Communicate uncertainty and limitations",
            ],
            prerequisites=["Spreadsheet fluency", "Basic SQL or Python"],
            active=True,
            is_demo=True,
        )
        for ordinal, title, summary, exercise in [
            (
                1,
                "Source and metric audit",
                "Test completeness, validity, uniqueness, and freshness.",
                "Profile a fictional grants dataset and write a prioritized issue log.",
            ),
            (
                2,
                "Analysis that survives review",
                "Connect every conclusion to a reproducible calculation.",
                "Build three metrics with definitions, SQL or formulas, and edge-case tests.",
            ),
            (
                3,
                "Decision-ready dashboard",
                "Design hierarchy around decisions rather than chart volume.",
                "Produce a one-page dashboard and a five-sentence executive interpretation.",
            ),
        ]:
            await upsert(
                session,
                LearningModule,
                f"learning-module-data-{ordinal}",
                learning_path_id=data_path.id,
                ordinal=ordinal,
                title=title,
                summary=summary,
                estimated_minutes=180,
                content_sections=[
                    {"title": "Professional standard", "body": summary},
                    {
                        "title": "Review habit",
                        "body": "State the source, calculation, caveat, and decision implication explicitly.",
                    },
                ],
                exercise_brief=exercise,
                completion_evidence="A reviewable artifact and a written explanation of key choices.",
            )
        api_path = await upsert(
            session,
            LearningPath,
            "learning-path-api-collaboration",
            slug="api-delivery-and-team-collaboration",
            title="API delivery and team collaboration",
            summary=(
                "Practice typed API contracts, authorization boundaries, failure handling, code "
                "review, and concise delivery communication."
            ),
            level="INTERMEDIATE",
            estimated_hours=18,
            skill_outcomes=[
                "Design validated API contracts",
                "Enforce authorization and tenant boundaries",
                "Handle retries and partial failures",
                "Communicate progress and review evidence",
            ],
            prerequisites=["One programming language", "HTTP fundamentals"],
            active=True,
            is_demo=True,
        )
        for ordinal, title in enumerate(
            [
                "Typed boundaries",
                "Authorization and failure modes",
                "Team delivery and review",
            ],
            start=1,
        ):
            await upsert(
                session,
                LearningModule,
                f"learning-module-api-{ordinal}",
                learning_path_id=api_path.id,
                ordinal=ordinal,
                title=title,
                summary=f"Apply professional {title.lower()} practices to a small service.",
                estimated_minutes=210,
                content_sections=[
                    {
                        "title": title,
                        "body": (
                            "Make inputs, permissions, state changes, errors, and verification "
                            "observable at the boundary where they matter."
                        ),
                    }
                ],
                exercise_brief="Implement and review one constrained API workflow with meaningful tests.",
                completion_evidence="Code evidence, test output, and a short review note.",
            )

        enrollment = await upsert(
            session,
            LearningEnrollment,
            "learning-enrollment-amina-frontend",
            learning_path_id=frontend_path.id,
            student_user_id=users["student"].id,
            status="IN_PROGRESS",
            enrolled_at=datetime.now(UTC) - timedelta(days=4),
            completed_at=None,
        )
        await upsert(
            session,
            LearningModuleCompletion,
            "learning-completion-amina-brief",
            enrollment_id=enrollment.id,
            learning_module_id=frontend_modules[0].id,
            evidence_summary=(
                "Converted a fictional employer request into five observable criteria, two "
                "exclusions, and prioritized clarification questions."
            ),
            completed_at=datetime.now(UTC) - timedelta(days=2),
        )

        opportunity_project = await upsert(
            session,
            Project,
            "project-opportunity-accessibility",
            client_organization_id=client_org.id,
            created_by_id=users["client"].id,
            title="Accessibility resource finder",
            description=(
                "Create a responsive directory that helps residents find verified accessibility "
                "services using fictional public data."
            ),
            category="website",
            state=ProjectState.DRAFT.value,
            version=1,
            required_deposit_minor=0,
            funded_minor=0,
            currency="USD",
            complexity="MEDIUM",
            is_demo=True,
        )
        await upsert(
            session,
            ProjectOpportunity,
            "opportunity-accessibility",
            project_id=opportunity_project.id,
            published_by_id=users["client"].id,
            headline="Build an accessible community resource finder",
            brief=(
                "Northstar Civic Studio needs a responsive directory for a fictional community "
                "program. Users must browse by service category, search by keyword, understand "
                "eligibility notes, and use the complete flow with keyboard and screen reader. "
                "The work uses approved demo data and will be reviewed by a technical lead."
            ),
            required_skills=["TypeScript", "Responsive UI", "Accessibility", "Testing"],
            nice_to_have_skills=["Next.js", "Content design"],
            deliverables=[
                "Responsive resource directory",
                "Search and category filters",
                "Accessibility test evidence",
                "Deployment and handoff notes",
            ],
            proposal_requirements=[
                "Explain the component and data approach",
                "Provide one relevant work sample",
                "Propose milestones and availability",
                "State the fixed project amount",
            ],
            estimated_hours_low=22,
            estimated_hours_high=32,
            budget_minor=240_000,
            currency="USD",
            deadline=datetime.now(UTC) + timedelta(days=24),
            supervision_level="guided",
            status="OPEN",
            max_proposals=12,
        )
        proposal_project = await upsert(
            session,
            Project,
            "project-opportunity-content-workflow",
            client_organization_id=client_org.id,
            created_by_id=users["client"].id,
            title="Volunteer content approval workflow",
            description=(
                "Build a small authenticated workflow for drafting, reviewing, and approving "
                "fictional volunteer guidance content."
            ),
            category="crud_tool",
            state=ProjectState.DRAFT.value,
            version=1,
            required_deposit_minor=0,
            funded_minor=0,
            currency="USD",
            complexity="MEDIUM",
            is_demo=True,
        )
        proposal_opportunity = await upsert(
            session,
            ProjectOpportunity,
            "opportunity-content-workflow",
            project_id=proposal_project.id,
            published_by_id=users["client"].id,
            headline="Create a volunteer content approval workflow",
            brief=(
                "Design and implement a small authenticated tool where volunteer coordinators can "
                "draft guidance, request review, record feedback, and publish an approved version. "
                "The project requires clear permissions, audit history, responsive states, and tests."
            ),
            required_skills=[
                "TypeScript",
                "API integration",
                "Authorization",
                "Testing",
            ],
            nice_to_have_skills=["PostgreSQL", "UX writing"],
            deliverables=[
                "Authenticated workflow",
                "Audit timeline",
                "Automated tests",
            ],
            proposal_requirements=[
                "Describe authorization boundaries",
                "Show relevant API work",
            ],
            estimated_hours_low=28,
            estimated_hours_high=38,
            budget_minor=320_000,
            currency="USD",
            deadline=datetime.now(UTC) + timedelta(days=30),
            supervision_level="supported",
            status="OPEN",
            max_proposals=10,
        )
        await upsert(
            session,
            StudentProposal,
            "proposal-amina-content-workflow",
            opportunity_id=proposal_opportunity.id,
            student_user_id=users["student"].id,
            cover_note=(
                "I have built typed form workflows and can turn the permission rules into a "
                "small, reviewable implementation with explicit loading and denial states."
            ),
            approach=(
                "I would begin with the role and transition matrix, define the API contract, then "
                "implement the draft-review-publish path as one vertical slice. I would add tenant "
                "authorization tests before the secondary interface states and bind delivery evidence "
                "to the accepted criteria."
            ),
            delivery_plan=[
                {
                    "milestone": "Contract and permissions",
                    "outcome": "Approved workflow states and API boundaries.",
                },
                {
                    "milestone": "Core implementation",
                    "outcome": "Responsive draft, review, and publish workflows.",
                },
                {
                    "milestone": "Verification",
                    "outcome": "Authorization, accessibility, and release evidence.",
                },
            ],
            relevant_evidence=[
                {
                    "title": "Fictional grants portal contribution",
                    "url": "https://example.test/portfolio/grants-portal",
                    "relevance": "Demonstrates typed React forms, accessibility states, and review evidence.",
                }
            ],
            proposed_amount_minor=285_000,
            currency="USD",
            estimated_days=21,
            availability_hours_per_week=12,
            state="SUBMITTED",
            submission_idempotency_key="demo-amina-content-proposal",
            submission_hash="a" * 64,
            decided_by_id=None,
            decision_reason=None,
            decided_at=None,
            decision_idempotency_key=None,
        )

        active_project = await upsert(
            session,
            Project,
            "project-active",
            client_organization_id=client_org.id,
            created_by_id=users["client"].id,
            title="Community grants reporting portal",
            description=(
                "Build an accessible dashboard for a fictional community grants program "
                "with approved demo data only."
            ),
            category="dashboard",
            state=ProjectState.ACTIVE.value,
            version=10,
            required_deposit_minor=320000,
            funded_minor=320000,
            currency="USD",
            complexity="MEDIUM",
            is_demo=True,
        )
        offer = await upsert(
            session,
            AssignmentOffer,
            "offer-accepted",
            project_id=active_project.id,
            recipient_user_id=users["student"].id,
            role="frontend developer",
            state=OfferState.ACCEPTED.value,
            terms_snapshot={
                "scope_version": 1,
                "gross_compensation_minor": 180000,
                "currency": "USD",
                "expected_hours": {"low": 18, "high": 24},
                "expected_weekly_hours": 8,
                "deadline": str(date.today() + timedelta(days=28)),
                "revision_rounds": 2,
                "lead_user_id": str(users["lead"].id),
                "portfolio": "anonymized summary only",
                "is_demo": True,
            },
            expires_at=datetime.now(UTC) + timedelta(days=3),
            decided_at=datetime.now(UTC),
        )
        await upsert(
            session,
            ProjectAssignment,
            "assignment-student",
            project_id=active_project.id,
            user_id=users["student"].id,
            role="frontend developer",
            offer_id=offer.id,
        )
        lead_offer = await upsert(
            session,
            AssignmentOffer,
            "offer-lead",
            project_id=active_project.id,
            recipient_user_id=users["lead"].id,
            role="technical lead",
            state=OfferState.ACCEPTED.value,
            terms_snapshot={
                "gross_compensation_minor": 60000,
                "currency": "USD",
                "review_hours": 6,
                "conflict_declared": False,
                "is_demo": True,
            },
            expires_at=datetime.now(UTC) + timedelta(days=3),
            decided_at=datetime.now(UTC),
        )
        await upsert(
            session,
            ProjectAssignment,
            "assignment-lead",
            project_id=active_project.id,
            user_id=users["lead"].id,
            role="technical lead",
            offer_id=lead_offer.id,
        )
        await upsert(
            session,
            ConsentRecord,
            "consent-student-credential",
            user_id=users["student"].id,
            consent_type="credential_publication",
            version="demo-1",
            granted=True,
            snapshot={
                "display_name": True,
                "project_title": False,
                "public_evidence": "anonymized",
                "captured_in": "demo",
            },
        )
        await upsert(
            session,
            PortfolioPermission,
            "portfolio-active",
            project_id=active_project.id,
            student_user_id=users["student"].id,
            client_name_allowed=False,
            project_title_allowed=False,
            screenshots_allowed=False,
            repository_allowed=False,
            deployment_allowed=False,
            anonymized_summary_allowed=True,
            consent_snapshot={"version": "demo-1"},
        )

        completed_at = datetime(2026, 1, 15, 16, 0, tzinfo=UTC)
        completed_project = await upsert(
            session,
            Project,
            "project-completed",
            client_organization_id=client_org.id,
            created_by_id=users["client"].id,
            title="Accessible resource directory",
            description=(
                "A completed fictional directory project with immutable demo QA, "
                "acceptance, earnings, and credential evidence."
            ),
            category="website",
            state=ProjectState.COMPLETED.value,
            version=18,
            required_deposit_minor=180000,
            funded_minor=180000,
            currency="USD",
            complexity="LOW",
            is_demo=True,
        )
        completed_offer = await upsert(
            session,
            AssignmentOffer,
            "offer-completed-student",
            project_id=completed_project.id,
            recipient_user_id=users["student"].id,
            role="student developer",
            state=OfferState.ACCEPTED.value,
            terms_snapshot={
                "gross_compensation_minor": 120000,
                "currency": "USD",
                "expected_hours": {"low": 14, "high": 18},
                "revision_rounds": 2,
                "decline_reputation_impact": "none",
                "is_demo": True,
            },
            expires_at=completed_at - timedelta(days=30),
            decided_at=completed_at - timedelta(days=35),
        )
        await upsert(
            session,
            ProjectAssignment,
            "assignment-completed-student",
            project_id=completed_project.id,
            user_id=users["student"].id,
            role="student developer",
            offer_id=completed_offer.id,
        )
        completed_lead_offer = await upsert(
            session,
            AssignmentOffer,
            "offer-completed-lead",
            project_id=completed_project.id,
            recipient_user_id=users["lead"].id,
            role="technical lead",
            state=OfferState.ACCEPTED.value,
            terms_snapshot={
                "gross_compensation_minor": 30000,
                "currency": "USD",
                "review_hours": 3,
                "conflict_declared": False,
                "is_demo": True,
            },
            expires_at=completed_at - timedelta(days=30),
            decided_at=completed_at - timedelta(days=35),
        )
        await upsert(
            session,
            ProjectAssignment,
            "assignment-completed-lead",
            project_id=completed_project.id,
            user_id=users["lead"].id,
            role="technical lead",
            offer_id=completed_lead_offer.id,
        )
        completed_milestone = await upsert(
            session,
            Milestone,
            "milestone-completed",
            project_id=completed_project.id,
            title="Accessible directory release",
            ordinal=1,
            due_at=completed_at - timedelta(days=1),
            status="COMPLETED",
        )
        await upsert(
            session,
            Task,
            "task-completed",
            project_id=completed_project.id,
            milestone_id=completed_milestone.id,
            assignee_id=users["student"].id,
            title="Validate accessible directory workflow",
            definition_of_done=(
                "Automated checks, keyboard review, and accepted artifact evidence are recorded."
            ),
            state="DONE",
            dependency_ids=[],
            estimate_hours=16,
        )
        completed_log = await insert_immutable(
            session,
            WorkLog,
            "work-log-completed",
            project_id=completed_project.id,
            student_user_id=users["student"].id,
            minutes=960,
            description="Implemented and tested the approved fictional directory scope.",
            submitted_at=completed_at - timedelta(days=2),
        )
        completed_deliverable = await insert_immutable(
            session,
            Deliverable,
            "deliverable-completed",
            project_id=completed_project.id,
            submitted_by_id=users["student"].id,
            title="Resource directory release",
            status="ACCEPTED",
            version=1,
        )
        completed_artifact = await insert_immutable(
            session,
            DeliverableArtifact,
            "artifact-completed",
            deliverable_id=completed_deliverable.id,
            kind="repository",
            uri="https://example.invalid/praxisai-demo/resource-directory",
            commit_sha="f" * 40,
            content_hash="a" * 64,
            scan_status="CLEAN_DEMO_FIXTURE",
        )
        completed_qa = await insert_immutable(
            session,
            QAReview,
            "qa-completed",
            deliverable_id=completed_deliverable.id,
            artifact_id=completed_artifact.id,
            status="COMPLETED",
            recommendation="PASS",
            deterministic_evidence={
                "environment": "demo",
                "tests_passed": 18,
                "accessibility_checks": "passed demo fixture",
                "artifact_content_hash": completed_artifact.content_hash,
            },
            agent_run_id=None,
        )
        completed_lead_review = await insert_immutable(
            session,
            LeadReview,
            "lead-review-completed",
            project_id=completed_project.id,
            deliverable_id=completed_deliverable.id,
            lead_user_id=users["lead"].id,
            review_type="DELIVERABLE",
            recommendation="RELEASE",
            findings={
                "environment": "demo",
                "summary": "Evidence supports release of the fictional demo artifact.",
            },
            conflict_declared=False,
        )
        completed_decision = await insert_immutable(
            session,
            ClientDecision,
            "client-decision-completed",
            project_id=completed_project.id,
            deliverable_id=completed_deliverable.id,
            actor_id=users["client"].id,
            decision="ACCEPTED",
            reason="Fictional client accepted the demo deliverable evidence.",
            revision_round=0,
        )
        completed_transition = await insert_immutable(
            session,
            ProjectTransition,
            "transition-completed",
            project_id=completed_project.id,
            actor_id=users["coordinator"].id,
            previous_state=ProjectState.PAYOUT_PENDING.value,
            new_state=ProjectState.COMPLETED.value,
            reason="Demo payout evidence and acceptance gates were satisfied.",
            correlation_id=identifier("correlation-completed"),
            idempotency_key="demo-project-completed-v1",
        )
        await insert_immutable(
            session,
            Invoice,
            "invoice-completed",
            project_id=completed_project.id,
            number="DEMO-INV-2026-001",
            amount_minor=180000,
            currency="USD",
            status="FUNDED_EXTERNALLY",
            environment="demo",
        )
        payout_allocation = await insert_immutable(
            session,
            PayoutAllocation,
            "payout-allocation-completed",
            project_id=completed_project.id,
            recipient_user_id=users["student"].id,
            amount_minor=120000,
            currency="USD",
            status="APPROVED",
            approved_by_id=users["coordinator"].id,
        )
        await record_external_payout(
            session,
            allocation_id=payout_allocation.id,
            body=ExternalPayoutRequest(
                approved_arrangement=True,
                external_reference="demo-external-evidence-2026-001",
                evidence_summary=(
                    "Fictional demo evidence confirms an approved external payout record."
                ),
            ),
            principal=SessionPrincipal(
                users["admin"].id,
                ops_org.id,
                Role.PLATFORM_ADMIN.value,
            ),
            idempotency_key="demo-external-payout-2026-001",
            correlation_id=identifier("correlation-external-payout"),
        )
        await insert_immutable(
            session,
            Approval,
            "approval-active-release",
            project_id=active_project.id,
            subject_type="project_plan",
            subject_id=active_project.id,
            decision="PENDING",
            actor_id=users["coordinator"].id,
            reason="Fictional demo plan requires a human coordinator decision.",
        )
        await insert_immutable(
            session,
            ProjectRisk,
            "risk-active-access",
            project_id=active_project.id,
            source="deterministic",
            summary="Demo client access confirmation is due before the next milestone.",
            confidence="high",
            status="OPEN",
            human_decision=None,
            decided_by_id=None,
        )

        await seed_internship_demo(session, users=users, university=university)

        credential_permission = await upsert(
            session,
            PortfolioPermission,
            "portfolio-completed",
            project_id=completed_project.id,
            student_user_id=users["student"].id,
            client_name_allowed=False,
            project_title_allowed=False,
            screenshots_allowed=False,
            repository_allowed=False,
            deployment_allowed=False,
            anonymized_summary_allowed=True,
            consent_snapshot={"version": "demo-1", "environment": "demo"},
        )
        signer = DemoSigningProvider(settings.credential_demo_private_key_path)
        credential_payload, credential_hash, credential_signature, credential_slug = (
            build_signed_credential(
                signer=signer,
                issuer=settings.credential_issuer,
                student_display_name=users["student"].display_name,
                project_title="Private client project",
                role="student developer",
                contribution_summary=(
                    "Implemented and validated the approved fictional resource directory."
                ),
                skill_evidence=[
                    {
                        "evidence_id": str(completed_qa.id),
                        "skill": "Accessible web development",
                        "criterion": "Approved directory workflow",
                        "summary": (
                            "Passing deterministic demo QA is bound to the immutable "
                            "artifact content hash."
                        ),
                    }
                ],
                verified_minutes=completed_log.minutes,
                client_accepted_at=completed_at - timedelta(hours=2),
                completed_at=completed_at,
                public_artifacts=[],
                qa_summary=(
                    "Passing QA and technical-lead release evidence are bound to the "
                    "immutable demo artifact version."
                ),
                is_demo=True,
                credential_id=str(identifier("credential-completed")),
                public_slug="demo-accessible-resource-directory",
                issued_at=completed_at + timedelta(hours=1),
            )
        )
        credential = await upsert(
            session,
            Credential,
            "credential-completed",
            student_user_id=users["student"].id,
            project_id=completed_project.id,
            public_slug=credential_slug,
            status="VALID",
            schema_version="1.0",
            canonical_payload=credential_payload,
            payload_hash=credential_hash,
            signature=credential_signature,
            key_identifier=signer.key_identifier,
            consent_snapshot={
                **credential_permission.consent_snapshot,
                "client_name_allowed": False,
                "project_title_allowed": False,
            },
            issued_at=completed_at + timedelta(hours=1),
            revoked_at=None,
        )
        for evidence_type, evidence_id, public_payload in [
            (
                "qa_review",
                completed_qa.id,
                {
                    "recommendation": "PASS",
                    "artifact_hash": completed_artifact.content_hash,
                },
            ),
            (
                "lead_review",
                completed_lead_review.id,
                {"recommendation": "RELEASE", "conflict_declared": False},
            ),
            (
                "client_acceptance",
                completed_decision.id,
                {"decision": "ACCEPTED", "revision_round": 0},
            ),
            (
                "completion_transition",
                completed_transition.id,
                {"state": ProjectState.COMPLETED.value},
            ),
        ]:
            await insert_immutable(
                session,
                CredentialEvidence,
                f"credential-evidence-{evidence_type}",
                credential_id=credential.id,
                evidence_type=evidence_type,
                evidence_id=evidence_id,
                public_payload=public_payload,
            )

        waiting_project = await upsert(
            session,
            Project,
            "project-waiting",
            client_organization_id=client_org.id,
            created_by_id=users["client"].id,
            title="Volunteer onboarding workflow",
            description=(
                "Automate the intake and review workflow for a fictional volunteer "
                "organization using non-sensitive demo data."
            ),
            category="workflow_automation",
            state=ProjectState.AWAITING_STUDENT_ACCEPTANCE.value,
            version=7,
            required_deposit_minor=240000,
            funded_minor=240000,
            currency="USD",
            complexity="LOW",
            is_demo=True,
        )
        await upsert(
            session,
            AssignmentOffer,
            "offer-open",
            project_id=waiting_project.id,
            recipient_user_id=users["available"].id,
            role="automation developer",
            state=OfferState.OFFERED.value,
            terms_snapshot={
                "scope_version": 1,
                "gross_compensation_minor": 150000,
                "currency": "USD",
                "expected_hours": {"low": 14, "high": 20},
                "expected_weekly_hours": 7,
                "deadline": str(date.today() + timedelta(days=21)),
                "revision_rounds": 2,
                "portfolio": "anonymized summary only",
                "decline_reputation_impact": "none",
                "is_demo": True,
            },
            expires_at=datetime.now(UTC) + timedelta(days=3),
            decided_at=None,
        )
        await upsert(
            session,
            AssignmentOffer,
            "offer-declined",
            project_id=waiting_project.id,
            recipient_user_id=users["partial"].id,
            role="automation developer",
            state=OfferState.DECLINED.value,
            terms_snapshot={
                "gross_compensation_minor": 150000,
                "currency": "USD",
                "decline_reputation_impact": "none",
                "is_demo": True,
            },
            expires_at=datetime.now(UTC) + timedelta(days=2),
            decided_at=datetime.now(UTC),
        )
        for key, category, title, body, path in [
            (
                "client",
                "projects",
                "Scope decision requested",
                "A fictional demo project is ready for a client decision.",
                "/client/projects",
            ),
            (
                "student",
                "credentials",
                "Credential evidence reminder",
                "Review the fictional demo project's credential consent and evidence.",
                "/student/credentials",
            ),
            (
                "university",
                "operations",
                "Cohort report available",
                "Privacy-safe fictional demo cohort metrics are available for review.",
                "/university",
            ),
        ]:
            event_id = identifier(f"notification-event-{key}")
            if await session.get(OutboxEvent, event_id) is None:
                event = notification_event(
                    recipient_user_id=users[key].id,
                    category=category,
                    title=title,
                    body=body,
                    resource_path=path,
                    correlation_id=identifier(f"notification-correlation-{key}"),
                )
                event.id = event_id
                session.add(event)
        await session.commit()
        print("Seeded deterministic Demo data.")


if __name__ == "__main__":
    asyncio.run(seed())
