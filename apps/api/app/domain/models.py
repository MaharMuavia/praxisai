import uuid
from datetime import date, datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
    text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class EntityMixin:
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class User(EntityMixin, Base):
    __tablename__ = "users"
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(160))
    external_subject: Mapped[str | None] = mapped_column(String(255), unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)


class Organization(EntityMixin, Base):
    __tablename__ = "organizations"
    name: Mapped[str] = mapped_column(String(200))
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    kind: Mapped[str] = mapped_column(String(40))
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)


class OrganizationMembership(EntityMixin, Base):
    __tablename__ = "organization_memberships"
    __table_args__ = (UniqueConstraint("user_id", "organization_id", "role"),)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"), index=True)
    role: Mapped[str] = mapped_column(String(40), index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class StudentProfile(EntityMixin, Base):
    __tablename__ = "student_profiles"
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), unique=True)
    bio: Mapped[str] = mapped_column(Text, default="")
    timezone: Mapped[str] = mapped_column(String(80), default="UTC")
    eligible: Mapped[bool] = mapped_column(Boolean, default=True)
    confirmed_18_plus: Mapped[bool] = mapped_column(Boolean, default=False)
    workload_cap_hours: Mapped[int] = mapped_column(Integer, default=20)
    committed_hours: Mapped[int] = mapped_column(Integer, default=0)
    completed_projects: Mapped[int] = mapped_column(Integer, default=0)


class LeadProfile(EntityMixin, Base):
    __tablename__ = "lead_profiles"
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), unique=True)
    domains: Mapped[list[str]] = mapped_column(JSON, default=list)
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    workload_cap_hours: Mapped[int] = mapped_column(Integer, default=10)
    committed_hours: Mapped[int] = mapped_column(Integer, default=0)


class ClientProfile(EntityMixin, Base):
    __tablename__ = "client_profiles"
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), unique=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"), index=True)
    verification_status: Mapped[str] = mapped_column(String(32), default="UNVERIFIED")
    billing_country: Mapped[str | None] = mapped_column(String(2))


class ClientVerification(EntityMixin, Base):
    __tablename__ = "client_verifications"
    client_profile_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("client_profiles.id"), index=True
    )
    status: Mapped[str] = mapped_column(String(32), default="UNVERIFIED")
    evidence: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    reviewed_by_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Invitation(EntityMixin, Base):
    __tablename__ = "invitations"
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"), index=True)
    email: Mapped[str] = mapped_column(String(320), index=True)
    role: Mapped[str] = mapped_column(String(40))
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Skill(EntityMixin, Base):
    __tablename__ = "skills"
    name: Mapped[str] = mapped_column(String(100), unique=True)


class StudentSkill(EntityMixin, Base):
    __tablename__ = "student_skills"
    __table_args__ = (UniqueConstraint("student_profile_id", "skill_id"),)
    student_profile_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("student_profiles.id"), index=True
    )
    skill_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("skills.id"), index=True)
    proficiency: Mapped[int] = mapped_column(Integer)
    source: Mapped[str] = mapped_column(String(32), default="self_declared")
    evidence_count: Mapped[int] = mapped_column(Integer, default=0)


class AvailabilityWindow(EntityMixin, Base):
    __tablename__ = "availability_windows"
    student_profile_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("student_profiles.id"), index=True
    )
    starts_on: Mapped[date] = mapped_column(Date)
    ends_on: Mapped[date] = mapped_column(Date)
    hours_per_week: Mapped[int] = mapped_column(Integer)


class University(EntityMixin, Base):
    __tablename__ = "universities"
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"), unique=True)
    agreement_status: Mapped[str] = mapped_column(String(32), default="INACTIVE")


class InstitutionalAgreement(EntityMixin, Base):
    __tablename__ = "institutional_agreements"
    university_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("universities.id"), index=True)
    version: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(30))
    entitlements: Mapped[list[str]] = mapped_column(JSON, default=list)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class UniversityEnrollment(EntityMixin, Base):
    __tablename__ = "university_enrollments"
    university_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("universities.id"), index=True)
    student_profile_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("student_profiles.id"), index=True
    )
    consented: Mapped[bool] = mapped_column(Boolean, default=False)


class PolicyVersion(EntityMixin, Base):
    __tablename__ = "policy_versions"
    __table_args__ = (UniqueConstraint("policy_name", "version"),)
    policy_name: Mapped[str] = mapped_column(String(100))
    version: Mapped[int] = mapped_column(Integer)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON)
    active_from: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)


class LearningPath(EntityMixin, Base):
    __tablename__ = "learning_paths"
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(200))
    summary: Mapped[str] = mapped_column(Text)
    level: Mapped[str] = mapped_column(String(30))
    estimated_hours: Mapped[int] = mapped_column(Integer)
    skill_outcomes: Mapped[list[str]] = mapped_column(JSON, default=list)
    prerequisites: Mapped[list[str]] = mapped_column(JSON, default=list)
    active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)
    __table_args__ = (CheckConstraint("estimated_hours > 0"),)


class LearningModule(EntityMixin, Base):
    __tablename__ = "learning_modules"
    __table_args__ = (UniqueConstraint("learning_path_id", "ordinal"),)
    learning_path_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("learning_paths.id"), index=True)
    ordinal: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(200))
    summary: Mapped[str] = mapped_column(Text)
    estimated_minutes: Mapped[int] = mapped_column(Integer)
    content_sections: Mapped[list[dict[str, str]]] = mapped_column(JSON, default=list)
    exercise_brief: Mapped[str] = mapped_column(Text)
    completion_evidence: Mapped[str] = mapped_column(Text)


class LearningEnrollment(EntityMixin, Base):
    __tablename__ = "learning_enrollments"
    __table_args__ = (UniqueConstraint("learning_path_id", "student_user_id"),)
    learning_path_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("learning_paths.id"), index=True)
    student_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    status: Mapped[str] = mapped_column(String(30), default="IN_PROGRESS")
    enrolled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class LearningModuleCompletion(EntityMixin, Base):
    __tablename__ = "learning_module_completions"
    __table_args__ = (UniqueConstraint("enrollment_id", "learning_module_id"),)
    enrollment_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("learning_enrollments.id"), index=True
    )
    learning_module_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("learning_modules.id"), index=True
    )
    evidence_summary: Mapped[str] = mapped_column(Text)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class Project(EntityMixin, Base):
    __tablename__ = "projects"
    client_organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id"), index=True
    )
    created_by_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(80))
    state: Mapped[str] = mapped_column(String(64), default="DRAFT", index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    required_deposit_minor: Mapped[int] = mapped_column(Integer, default=0)
    funded_minor: Mapped[int] = mapped_column(Integer, default=0)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    complexity: Mapped[str] = mapped_column(String(20), default="LOW")
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)
    __table_args__ = (
        CheckConstraint("required_deposit_minor >= 0"),
        CheckConstraint("funded_minor >= 0"),
    )


class ProjectOpportunity(EntityMixin, Base):
    __tablename__ = "project_opportunities"
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id"), unique=True, index=True
    )
    published_by_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    headline: Mapped[str] = mapped_column(String(200))
    brief: Mapped[str] = mapped_column(Text)
    required_skills: Mapped[list[str]] = mapped_column(JSON, default=list)
    nice_to_have_skills: Mapped[list[str]] = mapped_column(JSON, default=list)
    deliverables: Mapped[list[str]] = mapped_column(JSON, default=list)
    proposal_requirements: Mapped[list[str]] = mapped_column(JSON, default=list)
    estimated_hours_low: Mapped[int] = mapped_column(Integer)
    estimated_hours_high: Mapped[int] = mapped_column(Integer)
    budget_minor: Mapped[int] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(3))
    deadline: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    supervision_level: Mapped[str] = mapped_column(String(30))
    status: Mapped[str] = mapped_column(String(30), default="OPEN", index=True)
    max_proposals: Mapped[int] = mapped_column(Integer, default=20)
    __table_args__ = (
        CheckConstraint("estimated_hours_low > 0"),
        CheckConstraint("estimated_hours_high >= estimated_hours_low"),
        CheckConstraint("budget_minor > 0"),
        CheckConstraint("max_proposals > 0"),
    )


class StudentProposal(EntityMixin, Base):
    __tablename__ = "student_proposals"
    opportunity_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("project_opportunities.id"), index=True
    )
    student_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    cover_note: Mapped[str] = mapped_column(Text)
    approach: Mapped[str] = mapped_column(Text)
    delivery_plan: Mapped[list[dict[str, str]]] = mapped_column(JSON)
    relevant_evidence: Mapped[list[dict[str, str]]] = mapped_column(JSON)
    proposed_amount_minor: Mapped[int] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(3))
    estimated_days: Mapped[int] = mapped_column(Integer)
    availability_hours_per_week: Mapped[int] = mapped_column(Integer)
    state: Mapped[str] = mapped_column(String(30), default="SUBMITTED", index=True)
    submission_idempotency_key: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    submission_hash: Mapped[str] = mapped_column(String(64))
    decided_by_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    decision_reason: Mapped[str | None] = mapped_column(Text)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    decision_idempotency_key: Mapped[str | None] = mapped_column(
        String(128), unique=True, index=True
    )
    __table_args__ = (
        UniqueConstraint("opportunity_id", "student_user_id"),
        CheckConstraint("proposed_amount_minor > 0"),
        CheckConstraint("estimated_days > 0"),
        CheckConstraint("availability_hours_per_week > 0"),
    )


class ProjectScopeVersion(EntityMixin, Base):
    __tablename__ = "project_scope_versions"
    __table_args__ = (UniqueConstraint("project_id", "version"),)
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id"), index=True)
    version: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(32), default="DRAFT")
    snapshot: Mapped[dict[str, Any]] = mapped_column(JSON)
    immutable_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AcceptanceCriterion(EntityMixin, Base):
    __tablename__ = "acceptance_criteria"
    scope_version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("project_scope_versions.id"), index=True
    )
    ordinal: Mapped[int] = mapped_column(Integer)
    description: Mapped[str] = mapped_column(Text)


class Quote(EntityMixin, Base):
    __tablename__ = "quotes"
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id"), index=True)
    scope_version_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("project_scope_versions.id"))
    version: Mapped[int] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(3))
    low_minor: Mapped[int] = mapped_column(Integer)
    base_minor: Mapped[int] = mapped_column(Integer)
    high_minor: Mapped[int] = mapped_column(Integer)
    revision_rounds: Mapped[int] = mapped_column(Integer, default=2)
    formula_version: Mapped[str] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(String(32), default="DRAFT")
    calculation_inputs: Mapped[dict[str, Any]] = mapped_column(JSON)
    __table_args__ = (UniqueConstraint("project_id", "version"),)


class QuoteLineItem(EntityMixin, Base):
    __tablename__ = "quote_line_items"
    quote_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("quotes.id"), index=True)
    kind: Mapped[str] = mapped_column(String(40))
    description: Mapped[str] = mapped_column(String(200))
    amount_minor: Mapped[int] = mapped_column(Integer)


class ProjectTransition(EntityMixin, Base):
    __tablename__ = "project_transitions"
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id"), index=True)
    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("organizations.id"), index=True
    )
    actor_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    operation: Mapped[str] = mapped_column(String(80), default="project.transition")
    previous_state: Mapped[str] = mapped_column(String(64))
    new_state: Mapped[str] = mapped_column(String(64))
    reason: Mapped[str] = mapped_column(Text)
    correlation_id: Mapped[uuid.UUID] = mapped_column(Uuid, index=True)
    request_hash: Mapped[str | None] = mapped_column(String(64), index=True)
    idempotency_key: Mapped[str] = mapped_column(String(128), unique=True)


class Approval(EntityMixin, Base):
    __tablename__ = "approvals"
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id"), index=True)
    subject_type: Mapped[str] = mapped_column(String(40))
    subject_id: Mapped[uuid.UUID] = mapped_column(Uuid, index=True)
    decision: Mapped[str] = mapped_column(String(20))
    actor_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    reason: Mapped[str] = mapped_column(Text)


class AuditEvent(EntityMixin, Base):
    __tablename__ = "audit_events"
    actor_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), index=True)
    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("organizations.id"), index=True
    )
    action: Mapped[str] = mapped_column(String(100), index=True)
    resource_type: Mapped[str] = mapped_column(String(80))
    resource_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, index=True)
    correlation_id: Mapped[uuid.UUID] = mapped_column(Uuid, index=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)


class PromptVersion(EntityMixin, Base):
    __tablename__ = "prompt_versions"
    agent_name: Mapped[str] = mapped_column(String(50), index=True)
    version: Mapped[str] = mapped_column(String(40))
    template: Mapped[str] = mapped_column(Text)
    active: Mapped[bool] = mapped_column(Boolean, default=False)
    __table_args__ = (UniqueConstraint("agent_name", "version"),)


class AgentRun(EntityMixin, Base):
    __tablename__ = "agent_runs"
    project_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("projects.id"), index=True)
    agent_name: Mapped[str] = mapped_column(String(50), index=True)
    status: Mapped[str] = mapped_column(String(30), index=True)
    model_identifier: Mapped[str | None] = mapped_column(String(120))
    prompt_version: Mapped[str] = mapped_column(String(40))
    input_snapshot_hash: Mapped[str] = mapped_column(String(64))
    input_summary: Mapped[dict[str, Any]] = mapped_column(JSON)
    output: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    validation_status: Mapped[str] = mapped_column(String(30))
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    usage: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    error_category: Mapped[str | None] = mapped_column(String(60))
    correlation_id: Mapped[uuid.UUID] = mapped_column(Uuid, index=True)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)
    runtime_version: Mapped[str] = mapped_column(String(40), default="runtime-v1")
    provider: Mapped[str] = mapped_column(String(40), default="unknown")
    resource_version: Mapped[int | None] = mapped_column(Integer)
    stale_result: Mapped[bool] = mapped_column(Boolean, default=False)
    human_approval_required: Mapped[bool] = mapped_column(Boolean, default=True)
    proposed_actions: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    executed_action_evidence: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)


class StaffingRun(EntityMixin, Base):
    __tablename__ = "staffing_runs"
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id"), index=True)
    scope_version_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("project_scope_versions.id"))
    status: Mapped[str] = mapped_column(String(30))
    weights_version: Mapped[str] = mapped_column(String(40))


class StaffingCandidate(EntityMixin, Base):
    __tablename__ = "staffing_candidates"
    staffing_run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("staffing_runs.id"), index=True)
    student_profile_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("student_profiles.id"), index=True
    )
    score_basis_points: Mapped[int] = mapped_column(Integer)
    confidence: Mapped[str] = mapped_column(String(20))
    components: Mapped[dict[str, int]] = mapped_column(JSON)
    explanation: Mapped[str] = mapped_column(Text)


class PlanRun(EntityMixin, Base):
    __tablename__ = "plan_runs"
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id"), index=True)
    scope_version_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("project_scope_versions.id"))
    agent_run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("agent_runs.id"))
    status: Mapped[str] = mapped_column(String(30))
    plan_snapshot: Mapped[dict[str, Any]] = mapped_column(JSON)


class AssignmentOffer(EntityMixin, Base):
    __tablename__ = "assignment_offers"
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id"), index=True)
    recipient_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    role: Mapped[str] = mapped_column(String(50))
    state: Mapped[str] = mapped_column(String(30), default="DRAFT")
    terms_snapshot: Mapped[dict[str, Any]] = mapped_column(JSON)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    decision_idempotency_key: Mapped[str | None] = mapped_column(
        String(128), unique=True, index=True
    )


class ProjectAssignment(EntityMixin, Base):
    __tablename__ = "project_assignments"
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id"), index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    role: Mapped[str] = mapped_column(String(50))
    offer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("assignment_offers.id"), unique=True)


class Milestone(EntityMixin, Base):
    __tablename__ = "milestones"
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    ordinal: Mapped[int] = mapped_column(Integer)
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(30), default="PLANNED")


class Task(EntityMixin, Base):
    __tablename__ = "tasks"
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id"), index=True)
    milestone_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("milestones.id"), index=True)
    assignee_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    definition_of_done: Mapped[str] = mapped_column(Text)
    state: Mapped[str] = mapped_column(String(30), default="BACKLOG")
    dependency_ids: Mapped[list[str]] = mapped_column(JSON, default=list)
    estimate_hours: Mapped[int] = mapped_column(Integer, default=1)


class CheckIn(EntityMixin, Base):
    __tablename__ = "check_ins"
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id"), index=True)
    student_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    progress: Mapped[str] = mapped_column(Text)
    next_step: Mapped[str] = mapped_column(Text)
    blocker: Mapped[str | None] = mapped_column(Text)
    help_needed: Mapped[str | None] = mapped_column(Text)


class ProjectRisk(EntityMixin, Base):
    __tablename__ = "project_risks"
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id"), index=True)
    source: Mapped[str] = mapped_column(String(30))
    summary: Mapped[str] = mapped_column(Text)
    confidence: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(30), default="OPEN")
    human_decision: Mapped[str | None] = mapped_column(String(30))
    decided_by_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))


class ProjectComment(EntityMixin, Base):
    __tablename__ = "project_comments"
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id"), index=True)
    author_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    visibility: Mapped[str] = mapped_column(String(30))
    body: Mapped[str] = mapped_column(Text)


class WorkLog(EntityMixin, Base):
    __tablename__ = "work_logs"
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id"), index=True)
    student_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    minutes: Mapped[int] = mapped_column(Integer)
    description: Mapped[str] = mapped_column(Text)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Deliverable(EntityMixin, Base):
    __tablename__ = "deliverables"
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id"), index=True)
    submitted_by_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    title: Mapped[str] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(30), default="SUBMITTED")
    version: Mapped[int] = mapped_column(Integer, default=1)


class DeliverableArtifact(EntityMixin, Base):
    __tablename__ = "deliverable_artifacts"
    deliverable_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("deliverables.id"), index=True)
    kind: Mapped[str] = mapped_column(String(30))
    uri: Mapped[str] = mapped_column(Text)
    commit_sha: Mapped[str | None] = mapped_column(String(64))
    content_hash: Mapped[str] = mapped_column(String(64))
    scan_status: Mapped[str] = mapped_column(String(30), default="NOT_SCANNED")


class QAReview(EntityMixin, Base):
    __tablename__ = "qa_reviews"
    deliverable_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("deliverables.id"), index=True)
    artifact_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("deliverable_artifacts.id"))
    status: Mapped[str] = mapped_column(String(30))
    recommendation: Mapped[str] = mapped_column(String(30))
    deterministic_evidence: Mapped[dict[str, Any]] = mapped_column(JSON)
    agent_run_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("agent_runs.id"))


class QAFinding(EntityMixin, Base):
    __tablename__ = "qa_findings"
    qa_review_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("qa_reviews.id"), index=True)
    criterion_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("acceptance_criteria.id"))
    source: Mapped[str] = mapped_column(String(30))
    severity: Mapped[str] = mapped_column(String(20))
    summary: Mapped[str] = mapped_column(Text)
    evidence: Mapped[dict[str, Any]] = mapped_column(JSON)


class LeadReview(EntityMixin, Base):
    __tablename__ = "lead_reviews"
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id"), index=True)
    deliverable_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("deliverables.id"))
    lead_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    review_type: Mapped[str] = mapped_column(String(30))
    recommendation: Mapped[str] = mapped_column(String(30))
    findings: Mapped[dict[str, Any]] = mapped_column(JSON)
    conflict_declared: Mapped[bool] = mapped_column(Boolean, default=False)


class ClientDecision(EntityMixin, Base):
    __tablename__ = "client_decisions"
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id"), index=True)
    deliverable_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("deliverables.id"))
    actor_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    decision: Mapped[str] = mapped_column(String(30))
    reason: Mapped[str] = mapped_column(Text)
    revision_round: Mapped[int] = mapped_column(Integer, default=0)


class ScopeChangeRequest(EntityMixin, Base):
    __tablename__ = "scope_change_requests"
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id"), index=True)
    requested_by_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    request_text: Mapped[str] = mapped_column(Text)
    classification: Mapped[str] = mapped_column(String(40))
    evidence: Mapped[dict[str, Any]] = mapped_column(JSON)
    classified_by_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))


class ChangeOrder(EntityMixin, Base):
    __tablename__ = "change_orders"
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id"), index=True)
    version: Mapped[int] = mapped_column(Integer)
    state: Mapped[str] = mapped_column(String(40), default="DRAFT")
    scope_diff: Mapped[dict[str, Any]] = mapped_column(JSON)
    added_compensation_minor: Mapped[int] = mapped_column(Integer)
    added_days: Mapped[int] = mapped_column(Integer)


class Invoice(EntityMixin, Base):
    __tablename__ = "invoices"
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id"), index=True)
    number: Mapped[str] = mapped_column(String(60), unique=True)
    amount_minor: Mapped[int] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(3))
    status: Mapped[str] = mapped_column(String(30))
    environment: Mapped[str] = mapped_column(String(20))


class PaymentEvent(EntityMixin, Base):
    __tablename__ = "payment_events"
    provider: Mapped[str] = mapped_column(String(30))
    provider_event_id: Mapped[str] = mapped_column(String(255), unique=True)
    project_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("projects.id"), index=True)
    event_type: Mapped[str] = mapped_column(String(80))
    environment: Mapped[str] = mapped_column(String(20))
    payload_hash: Mapped[str] = mapped_column(String(64))
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class LedgerEntry(EntityMixin, Base):
    __tablename__ = "ledger_entries"
    transaction_id: Mapped[uuid.UUID] = mapped_column(Uuid, index=True)
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id"), index=True)
    account: Mapped[str] = mapped_column(String(80))
    amount_minor: Mapped[int] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(3))
    memo: Mapped[str] = mapped_column(String(255))


class PayoutAllocation(EntityMixin, Base):
    __tablename__ = "payout_allocations"
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id"), index=True)
    recipient_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    amount_minor: Mapped[int] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(3))
    status: Mapped[str] = mapped_column(String(30), default="PENDING")
    approved_by_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))


class Payout(EntityMixin, Base):
    __tablename__ = "payouts"
    allocation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("payout_allocations.id"), unique=True, index=True
    )
    provider_reference: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(30))
    failure_reason: Mapped[str | None] = mapped_column(Text)
    evidence_hash: Mapped[str | None] = mapped_column(String(64))
    idempotency_key: Mapped[str | None] = mapped_column(String(128), unique=True, index=True)


class Appeal(EntityMixin, Base):
    __tablename__ = "appeals"
    appellant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id"), index=True)
    decision_type: Mapped[str] = mapped_column(String(50))
    decision_id: Mapped[uuid.UUID] = mapped_column(Uuid)
    state: Mapped[str] = mapped_column(String(40), default="OPEN")
    decision_snapshot: Mapped[dict[str, Any]] = mapped_column(JSON)
    reviewer_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    resolution_reason: Mapped[str | None] = mapped_column(Text)


class AppealEvidence(EntityMixin, Base):
    __tablename__ = "appeal_evidence"
    appeal_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("appeals.id"), index=True)
    submitted_by_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    evidence_type: Mapped[str] = mapped_column(String(40))
    payload: Mapped[dict[str, Any]] = mapped_column(JSON)


class Dispute(EntityMixin, Base):
    __tablename__ = "disputes"
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id"), index=True)
    opened_by_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    state: Mapped[str] = mapped_column(String(30), default="OPEN")
    category: Mapped[str] = mapped_column(String(50))
    summary: Mapped[str] = mapped_column(Text)
    reviewer_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    resolution: Mapped[str | None] = mapped_column(Text)


class ReputationEvent(EntityMixin, Base):
    __tablename__ = "reputation_events"
    student_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id"), index=True)
    dimension: Mapped[str] = mapped_column(String(40))
    value: Mapped[int] = mapped_column(Integer)
    evidence_type: Mapped[str] = mapped_column(String(50))
    evidence_id: Mapped[uuid.UUID] = mapped_column(Uuid)
    approved_by_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    reversed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ConsentRecord(EntityMixin, Base):
    __tablename__ = "consent_records"
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    consent_type: Mapped[str] = mapped_column(String(60))
    version: Mapped[str] = mapped_column(String(30))
    granted: Mapped[bool] = mapped_column(Boolean)
    snapshot: Mapped[dict[str, Any]] = mapped_column(JSON)


class PortfolioPermission(EntityMixin, Base):
    __tablename__ = "portfolio_permissions"
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id"), index=True)
    student_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    client_name_allowed: Mapped[bool] = mapped_column(Boolean, default=False)
    project_title_allowed: Mapped[bool] = mapped_column(Boolean, default=False)
    screenshots_allowed: Mapped[bool] = mapped_column(Boolean, default=False)
    repository_allowed: Mapped[bool] = mapped_column(Boolean, default=False)
    deployment_allowed: Mapped[bool] = mapped_column(Boolean, default=False)
    anonymized_summary_allowed: Mapped[bool] = mapped_column(Boolean, default=True)
    consent_snapshot: Mapped[dict[str, Any]] = mapped_column(JSON)


class Credential(EntityMixin, Base):
    __tablename__ = "credentials"
    student_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id"), index=True)
    public_slug: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    status: Mapped[str] = mapped_column(String(20), default="VALID")
    schema_version: Mapped[str] = mapped_column(String(20))
    canonical_payload: Mapped[dict[str, Any]] = mapped_column(JSON)
    payload_hash: Mapped[str] = mapped_column(String(64))
    signature: Mapped[str] = mapped_column(Text)
    key_identifier: Mapped[str] = mapped_column(String(255))
    consent_snapshot: Mapped[dict[str, Any]] = mapped_column(JSON)
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class CredentialEvidence(EntityMixin, Base):
    __tablename__ = "credential_evidence"
    credential_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("credentials.id"), index=True)
    evidence_type: Mapped[str] = mapped_column(String(40))
    evidence_id: Mapped[uuid.UUID] = mapped_column(Uuid)
    public_payload: Mapped[dict[str, Any]] = mapped_column(JSON)


class CredentialRevocation(EntityMixin, Base):
    __tablename__ = "credential_revocations"
    credential_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("credentials.id"), unique=True, index=True
    )
    revoked_by_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    reason: Mapped[str] = mapped_column(Text)
    idempotency_key: Mapped[str] = mapped_column(String(128), unique=True)
    revoked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class AgentRunEvent(EntityMixin, Base):
    __tablename__ = "agent_run_events"
    agent_run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("agent_runs.id"), index=True)
    event_type: Mapped[str] = mapped_column(String(50))
    payload: Mapped[dict[str, Any]] = mapped_column(JSON)


class RateCard(EntityMixin, Base):
    __tablename__ = "rate_cards"
    version: Mapped[int] = mapped_column(Integer, unique=True)
    currency: Mapped[str] = mapped_column(String(3))
    entries: Mapped[dict[str, Any]] = mapped_column(JSON)
    active_from: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class MatchingConfiguration(EntityMixin, Base):
    __tablename__ = "matching_configurations"
    version: Mapped[int] = mapped_column(Integer, unique=True)
    weights: Mapped[dict[str, int]] = mapped_column(JSON)
    active_from: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class FeatureFlag(EntityMixin, Base):
    __tablename__ = "feature_flags"
    name: Mapped[str] = mapped_column(String(100), unique=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    environment: Mapped[str] = mapped_column(String(20))
    reason: Mapped[str] = mapped_column(Text)


class AnalyticsEvent(EntityMixin, Base):
    __tablename__ = "analytics_events"
    event_type: Mapped[str] = mapped_column(String(80), index=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    environment: Mapped[str] = mapped_column(String(20))
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON)
    exported_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ExportJob(EntityMixin, Base):
    __tablename__ = "export_jobs"
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"), index=True)
    requested_by_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    purpose: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30))
    storage_key: Mapped[str | None] = mapped_column(String(500))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    idempotency_key: Mapped[str] = mapped_column(String(128), unique=True)


class RetentionConfiguration(EntityMixin, Base):
    __tablename__ = "retention_configurations"
    record_type: Mapped[str] = mapped_column(String(80), unique=True)
    retention_days: Mapped[int] = mapped_column(Integer)
    legal_review_required: Mapped[bool] = mapped_column(Boolean, default=True)
    active_from: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class Notification(EntityMixin, Base):
    __tablename__ = "notifications"
    __table_args__ = (UniqueConstraint("user_id", "source_outbox_event_id"),)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    kind: Mapped[str] = mapped_column(String(50))
    title: Mapped[str] = mapped_column(String(160))
    body: Mapped[str] = mapped_column(Text)
    resource_path: Mapped[str | None] = mapped_column(String(500))
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    source_outbox_event_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("outbox_events.id"), index=True
    )


class NotificationPreference(EntityMixin, Base):
    __tablename__ = "notification_preferences"
    __table_args__ = (UniqueConstraint("user_id", "category"),)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    category: Mapped[str] = mapped_column(String(40))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)


class OutboxEvent(EntityMixin, Base):
    __tablename__ = "outbox_events"
    event_type: Mapped[str] = mapped_column(String(80), index=True)
    aggregate_type: Mapped[str] = mapped_column(String(60))
    aggregate_id: Mapped[uuid.UUID] = mapped_column(Uuid, index=True)
    correlation_id: Mapped[uuid.UUID] = mapped_column(Uuid, default=uuid.uuid4, index=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(30), default="PENDING", index=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    available_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    last_error: Mapped[str | None] = mapped_column(Text)


class JobAttempt(EntityMixin, Base):
    __tablename__ = "job_attempts"
    __table_args__ = (UniqueConstraint("outbox_event_id", "attempt_number"),)
    outbox_event_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("outbox_events.id"), index=True)
    attempt_number: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(30), index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_category: Mapped[str | None] = mapped_column(String(100))
    error_message: Mapped[str | None] = mapped_column(Text)


class OutboxRecovery(EntityMixin, Base):
    __tablename__ = "outbox_recoveries"
    outbox_event_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("outbox_events.id"), index=True)
    recovered_by_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    reason: Mapped[str] = mapped_column(Text)
    idempotency_key: Mapped[str] = mapped_column(String(128), unique=True)
    recovered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class ProviderSynchronization(EntityMixin, Base):
    __tablename__ = "provider_synchronizations"
    provider: Mapped[str] = mapped_column(String(60), index=True)
    operation: Mapped[str] = mapped_column(String(80))
    mode: Mapped[str] = mapped_column(String(30))
    status: Mapped[str] = mapped_column(String(30), index=True)
    resource_type: Mapped[str] = mapped_column(String(60))
    resource_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, index=True)
    correlation_id: Mapped[uuid.UUID] = mapped_column(Uuid, index=True)
    error_category: Mapped[str | None] = mapped_column(String(100))
    details: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class PublicIntakeSubmission(EntityMixin, Base):
    __tablename__ = "public_intake_submissions"
    kind: Mapped[str] = mapped_column(String(32), index=True)
    status: Mapped[str] = mapped_column(String(32), default="NEW", index=True)
    contact_email: Mapped[str | None] = mapped_column(String(320), index=True)
    source: Mapped[str | None] = mapped_column(String(120))
    campaign: Mapped[str | None] = mapped_column(String(120))
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    consent_snapshot: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    idempotency_key: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    correlation_id: Mapped[uuid.UUID] = mapped_column(Uuid, index=True)
    owner_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), index=True)
    qualification_notes: Mapped[str | None] = mapped_column(Text)
    rejection_reason: Mapped[str | None] = mapped_column(Text)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    payload_hash: Mapped[str] = mapped_column(String(64), default="", index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    conversion_evidence: Mapped[str | None] = mapped_column(Text)
    retention_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    anonymized_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    withdrawal_requested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class PublicIntakeIdempotency(EntityMixin, Base):
    __tablename__ = "public_intake_idempotencies"
    idempotency_key: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    payload_hash: Mapped[str] = mapped_column(String(64))
    kind: Mapped[str] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(20), default="RESERVED", index=True)
    submission_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("public_intake_submissions.id"), unique=True, nullable=True
    )
    correlation_id: Mapped[uuid.UUID] = mapped_column(Uuid, index=True)


class RateLimitBucket(EntityMixin, Base):
    __tablename__ = "rate_limit_buckets"
    bucket_key: Mapped[str] = mapped_column(String(128), unique=True)
    window_started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    request_count: Mapped[int] = mapped_column(Integer, default=0)


class UniversityEmailDomain(EntityMixin, Base):
    __tablename__ = "university_email_domains"
    __table_args__ = (UniqueConstraint("university_id", "domain"),)
    university_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("universities.id"), index=True)
    domain: Mapped[str] = mapped_column(String(255), index=True)
    status: Mapped[str] = mapped_column(String(20), default="PENDING", index=True)
    allow_subdomains: Mapped[bool] = mapped_column(Boolean, default=False)
    verification_method: Mapped[str] = mapped_column(String(40), default="manual")
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    verified_by_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))


class AllowedStudentEmail(EntityMixin, Base):
    __tablename__ = "allowed_student_emails"
    __table_args__ = (UniqueConstraint("cohort_id", "email"),)
    cohort_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("internship_cohorts.id"), index=True)
    email: Mapped[str] = mapped_column(String(320), index=True)
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE", index=True)
    invitation_source: Mapped[str | None] = mapped_column(String(120))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class InternshipProgram(EntityMixin, Base):
    __tablename__ = "internship_programs"
    slug: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(220))
    public_description: Mapped[str] = mapped_column(Text)
    internal_description: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(30), default="DRAFT", index=True)
    default_timezone: Mapped[str] = mapped_column(String(80), default="UTC")
    duration_weeks: Mapped[int] = mapped_column(Integer)
    application_opens_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    application_closes_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    minimum_age: Mapped[int | None] = mapped_column(Integer)
    university_email_policy: Mapped[str] = mapped_column(String(30), default="REVIEW")
    personal_email_exception_policy: Mapped[str] = mapped_column(String(30), default="REVIEW")
    completion_policy_version: Mapped[str] = mapped_column(String(30), default="1.0")
    certificate_policy_version: Mapped[str] = mapped_column(String(30), default="1.0")
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)


class InternshipTrack(EntityMixin, Base):
    __tablename__ = "internship_tracks"
    slug: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(180))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)


class InternshipTrackVersion(EntityMixin, Base):
    __tablename__ = "internship_track_versions"
    __table_args__ = (UniqueConstraint("track_id", "version"),)
    track_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("internship_tracks.id"), index=True)
    version: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(200))
    summary: Mapped[str] = mapped_column(Text)
    prerequisites: Mapped[list[str]] = mapped_column(JSON, default=list)
    skill_outcomes: Mapped[list[str]] = mapped_column(JSON, default=list)
    expected_weekly_hours: Mapped[int] = mapped_column(Integer, default=10)
    status: Mapped[str] = mapped_column(String(30), default="DRAFT", index=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    published_by_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    learning_path_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("learning_paths.id"))
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)


class InternshipCohort(EntityMixin, Base):
    __tablename__ = "internship_cohorts"
    __table_args__ = (UniqueConstraint("program_id", "slug"),)
    program_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("internship_programs.id"), index=True)
    name: Mapped[str] = mapped_column(String(220))
    slug: Mapped[str] = mapped_column(String(120), index=True)
    timezone: Mapped[str] = mapped_column(String(80), default="UTC")
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    capacity: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(30), default="DRAFT", index=True)
    application_deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    enrollment_deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    late_policy: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    resubmission_policy: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    certificate_policy: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    coordinator_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)


class CohortTrack(EntityMixin, Base):
    __tablename__ = "internship_cohort_tracks"
    __table_args__ = (UniqueConstraint("cohort_id", "track_version_id"),)
    cohort_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("internship_cohorts.id"), index=True)
    track_version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("internship_track_versions.id"), index=True
    )
    capacity: Mapped[int] = mapped_column(Integer)
    reviewer_pool: Mapped[list[str]] = mapped_column(JSON, default=list)
    instructor_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))


class InternshipApplication(EntityMixin, Base):
    __tablename__ = "internship_applications"
    __table_args__ = (UniqueConstraint("applicant_user_id", "cohort_id"),)
    applicant_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    program_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("internship_programs.id"), index=True)
    cohort_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("internship_cohorts.id"), index=True)
    primary_track_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("internship_tracks.id"))
    secondary_track_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("internship_tracks.id"))
    education_status: Mapped[str] = mapped_column(String(80), default="")
    university_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("universities.id"))
    degree_program: Mapped[str] = mapped_column(String(180), default="")
    semester_status: Mapped[str] = mapped_column(String(180), default="")
    country: Mapped[str] = mapped_column(String(2), default="")
    timezone: Mapped[str] = mapped_column(String(80), default="UTC")
    weekly_availability_hours: Mapped[int | None] = mapped_column(Integer)
    technical_background: Mapped[str] = mapped_column(Text, default="")
    motivation: Mapped[str] = mapped_column(Text, default="")
    portfolio_url: Mapped[str | None] = mapped_column(String(500))
    github_url: Mapped[str | None] = mapped_column(String(500))
    linkedin_url: Mapped[str | None] = mapped_column(String(500))
    accessibility_requirements: Mapped[str | None] = mapped_column(Text)
    email_verification_evidence: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    consent_snapshot: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(40), default="DRAFT", index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    decision_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    decision_reason: Mapped[str | None] = mapped_column(Text)
    reviewer_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    correlation_id: Mapped[uuid.UUID] = mapped_column(Uuid, index=True)
    submit_idempotency_key: Mapped[str | None] = mapped_column(String(128), unique=True)


class CohortEnrollment(EntityMixin, Base):
    __tablename__ = "internship_cohort_enrollments"
    __table_args__ = (UniqueConstraint("cohort_id", "student_user_id"),)
    cohort_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("internship_cohorts.id"), index=True)
    student_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    track_version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("internship_track_versions.id"), index=True
    )
    status: Mapped[str] = mapped_column(String(30), default="INVITED", index=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    termination_reason: Mapped[str | None] = mapped_column(Text)
    progress_snapshot: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    certificate_eligibility: Mapped[str] = mapped_column(String(30), default="NOT_ELIGIBLE")
    version: Mapped[int] = mapped_column(Integer, default=1)
    completion_decision_idempotency_key: Mapped[str | None] = mapped_column(
        String(128), unique=True
    )
    completion_decision_reason: Mapped[str | None] = mapped_column(Text)


class InternshipPhase(EntityMixin, Base):
    __tablename__ = "internship_phases"
    __table_args__ = (UniqueConstraint("cohort_track_id", "ordinal"),)
    cohort_track_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("internship_cohort_tracks.id"), index=True
    )
    name: Mapped[str] = mapped_column(String(180))
    phase_type: Mapped[str] = mapped_column(String(30))
    ordinal: Mapped[int] = mapped_column(Integer)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    completion_requirement: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)


class InternshipWeek(EntityMixin, Base):
    __tablename__ = "internship_weeks"
    __table_args__ = (UniqueConstraint("phase_id", "week_number"),)
    phase_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("internship_phases.id"), index=True)
    week_number: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(180))
    summary: Mapped[str] = mapped_column(Text)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    unlock_policy: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    required_unit_count: Mapped[int] = mapped_column(Integer, default=0)
    required_assignment_count: Mapped[int] = mapped_column(Integer, default=0)


class InternshipUnit(EntityMixin, Base):
    __tablename__ = "internship_units"
    __table_args__ = (UniqueConstraint("week_id", "ordinal", "version"),)
    week_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("internship_weeks.id"), index=True)
    ordinal: Mapped[int] = mapped_column(Integer)
    unit_type: Mapped[str] = mapped_column(String(30))
    title: Mapped[str] = mapped_column(String(220))
    summary: Mapped[str] = mapped_column(Text)
    objectives: Mapped[list[str]] = mapped_column(JSON, default=list)
    resources: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    practical_exercise: Mapped[str] = mapped_column(Text, default="")
    completion_rule: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    prerequisites: Mapped[list[str]] = mapped_column(JSON, default=list)
    release_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_required: Mapped[bool] = mapped_column(Boolean, default=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)


class InternshipUnitCompletion(EntityMixin, Base):
    __tablename__ = "internship_unit_completions"
    __table_args__ = (UniqueConstraint("enrollment_id", "unit_id"),)
    enrollment_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("internship_cohort_enrollments.id"), index=True
    )
    unit_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("internship_units.id"), index=True)
    evidence: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    approved_by_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))


class InternshipAssignmentTemplate(EntityMixin, Base):
    __tablename__ = "internship_assignment_templates"
    __table_args__ = (UniqueConstraint("track_version_id", "version", "title"),)
    track_version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("internship_track_versions.id"), index=True
    )
    week_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("internship_weeks.id"), index=True)
    title: Mapped[str] = mapped_column(String(220))
    summary: Mapped[str] = mapped_column(Text)
    problem_statement: Mapped[str] = mapped_column(Text)
    objectives: Mapped[list[str]] = mapped_column(JSON, default=list)
    required_skills: Mapped[list[str]] = mapped_column(JSON, default=list)
    estimated_effort_hours: Mapped[int] = mapped_column(Integer)
    starter_resources: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    constraints: Mapped[list[str]] = mapped_column(JSON, default=list)
    deliverables: Mapped[list[str]] = mapped_column(JSON, default=list)
    acceptance_criteria: Mapped[list[str]] = mapped_column(JSON, default=list)
    required_artifact_types: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    rubric: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    maximum_score: Mapped[int] = mapped_column(Integer, default=100)
    pass_score: Mapped[int] = mapped_column(Integer, default=70)
    late_policy: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    resubmission_policy: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    version: Mapped[int] = mapped_column(Integer, default=1)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)


class InternshipCohortAssignment(EntityMixin, Base):
    __tablename__ = "internship_cohort_assignments"
    __table_args__ = (UniqueConstraint("cohort_track_id", "template_id"),)
    template_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("internship_assignment_templates.id"), index=True
    )
    cohort_track_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("internship_cohort_tracks.id"), index=True
    )
    release_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    deadline: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    grace_period_minutes: Mapped[int] = mapped_column(Integer, default=0)
    review_deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(30), default="DRAFT", index=True)
    reviewer_pool: Mapped[list[str]] = mapped_column(JSON, default=list)
    publish_idempotency_key: Mapped[str | None] = mapped_column(String(128), unique=True)


class InternshipStudentAssignment(EntityMixin, Base):
    __tablename__ = "internship_student_assignments"
    __table_args__ = (UniqueConstraint("cohort_assignment_id", "student_user_id"),)
    cohort_assignment_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("internship_cohort_assignments.id"), index=True
    )
    student_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    state: Mapped[str] = mapped_column(String(30), default="LOCKED", index=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    current_submission_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey(
            "internship_submissions.id",
            name="fk_internship_student_assignments_current_submission",
            use_alter=True,
        ),
        index=True,
    )
    attempt_count: Mapped[int] = mapped_column(Integer, default=0)
    extension_state: Mapped[str] = mapped_column(String(30), default="NONE")
    final_result: Mapped[str | None] = mapped_column(String(30))
    version: Mapped[int] = mapped_column(Integer, default=1)


class InternshipUpload(EntityMixin, Base):
    __tablename__ = "internship_uploads"
    upload_id: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    owner_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    student_assignment_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("internship_student_assignments.id"), index=True
    )
    artifact_type: Mapped[str] = mapped_column(String(50))
    filename: Mapped[str] = mapped_column(String(255))
    content_type: Mapped[str] = mapped_column(String(120))
    size_bytes: Mapped[int] = mapped_column(Integer)
    sha256: Mapped[str | None] = mapped_column(String(64))
    storage_key: Mapped[str] = mapped_column(String(500))
    state: Mapped[str] = mapped_column(String(30), default="INITIATED", index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    scan_message: Mapped[str | None] = mapped_column(String(500))
    scan_provider: Mapped[str | None] = mapped_column(String(40))
    scanned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    scan_evidence: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)


class InternshipSubmission(EntityMixin, Base):
    __tablename__ = "internship_submissions"
    __table_args__ = (
        UniqueConstraint("student_assignment_id", "version"),
        Index(
            "uq_internship_submissions_one_active_draft",
            "student_assignment_id",
            unique=True,
            postgresql_where=text("state = 'DRAFT'"),
            sqlite_where=text("state = 'DRAFT'"),
        ),
    )
    student_assignment_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("internship_student_assignments.id"), index=True
    )
    student_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    state: Mapped[str] = mapped_column(String(30), default="DRAFT", index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    links: Mapped[dict[str, str]] = mapped_column(JSON, default=dict)
    text_fields: Mapped[dict[str, str]] = mapped_column(JSON, default=dict)
    artifact_upload_ids: Mapped[list[str]] = mapped_column(JSON, default=list)
    artifact_snapshot: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    canonical_hash: Mapped[str | None] = mapped_column(String(64), index=True)
    rubric_version: Mapped[int | None] = mapped_column(Integer)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    deadline_status: Mapped[str | None] = mapped_column(String(20))
    correlation_id: Mapped[uuid.UUID] = mapped_column(Uuid, index=True)
    finalize_idempotency_key: Mapped[str | None] = mapped_column(String(128), unique=True)
    previous_submission_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("internship_submissions.id"), index=True
    )
    change_summary: Mapped[str | None] = mapped_column(Text)


class InternshipReview(EntityMixin, Base):
    __tablename__ = "internship_reviews"
    student_assignment_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("internship_student_assignments.id"), index=True
    )
    submission_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("internship_submissions.id"), index=True
    )
    reviewer_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), index=True)
    status: Mapped[str] = mapped_column(String(30), default="ASSIGNED", index=True)
    scores: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    weighted_total: Mapped[int | None] = mapped_column(Integer)
    student_feedback: Mapped[str | None] = mapped_column(Text)
    private_notes: Mapped[str | None] = mapped_column(Text)
    conflict_declared: Mapped[bool] = mapped_column(Boolean, default=False)
    decision: Mapped[str | None] = mapped_column(String(30))
    finalized_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    idempotency_key: Mapped[str | None] = mapped_column(String(128), unique=True)


class InternshipCertificate(EntityMixin, Base):
    __tablename__ = "internship_certificates"
    __table_args__ = (UniqueConstraint("enrollment_id"), UniqueConstraint("public_slug"))
    enrollment_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("internship_cohort_enrollments.id"), index=True
    )
    student_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    state: Mapped[str] = mapped_column(String(30), default="NOT_ELIGIBLE", index=True)
    public_slug: Mapped[str | None] = mapped_column(String(100), index=True)
    public_payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    issued_by_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    issued_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_by_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revocation_reason: Mapped[str | None] = mapped_column(Text)
    idempotency_key: Mapped[str | None] = mapped_column(String(128), unique=True)


Index("ix_tasks_project_state", Task.project_id, Task.state)
Index("ix_agent_runs_project_status", AgentRun.project_id, AgentRun.status)
