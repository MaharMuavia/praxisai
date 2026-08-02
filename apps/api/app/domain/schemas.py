import uuid
from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from app.domain.enums import ProjectState


class ApiModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ErrorDetail(BaseModel):
    code: str
    message: str
    correlation_id: uuid.UUID
    details: dict[str, Any] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    error: ErrorDetail


class MembershipView(ApiModel):
    organization_id: uuid.UUID
    organization_name: str
    role: str


class SessionView(BaseModel):
    user_id: uuid.UUID
    display_name: str
    email: str
    active_membership: MembershipView
    capabilities: list[str]
    onboarding_state: str
    notification_count: int
    environment_label: str
    required_consent_versions: dict[str, str]


class LocalSessionRequest(BaseModel):
    user_id: uuid.UUID
    organization_id: uuid.UUID
    role: str


class FirebaseSessionRequest(BaseModel):
    id_token: str = Field(min_length=20)


class ProjectCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=20, max_length=20_000)
    category: str = Field(min_length=2, max_length=80)
    desired_outcome: str = Field(min_length=10, max_length=4_000)
    target_users: str = Field(min_length=2, max_length=2_000)
    deliverables: list[str] = Field(default_factory=list, max_length=20)
    constraints: list[str] = Field(default_factory=list, max_length=30)
    desired_deadline: date | None = None
    budget_guidance_minor: int | None = Field(default=None, ge=0)
    data_sensitivity: Literal["public", "internal", "confidential", "restricted"] = "internal"
    attachment_references: list[HttpUrl] = Field(default_factory=list, max_length=10)


class ProjectView(ApiModel):
    id: uuid.UUID
    client_organization_id: uuid.UUID
    title: str
    description: str
    category: str
    state: str
    version: int
    required_deposit_minor: int
    funded_minor: int
    currency: str
    complexity: str
    is_demo: bool
    created_at: datetime


class ProjectList(BaseModel):
    items: list[ProjectView]
    next_cursor: str | None = None


class TransitionRequest(BaseModel):
    to_state: ProjectState
    reason: str = Field(min_length=3, max_length=2_000)
    expected_version: int = Field(ge=1)


class ScopeDraft(BaseModel):
    normalized_title: str
    summary: str
    problem_statement: str
    deliverables: list[str]
    acceptance_criteria: list[str]
    assumptions: list[str]
    exclusions: list[str]
    dependencies: list[str]
    clarification_questions: list[str]
    required_skills: list[str]
    effort_low_hours: int = Field(ge=1, le=200)
    effort_high_hours: int = Field(ge=1, le=200)
    complexity: Literal["LOW", "MEDIUM", "HIGH"]
    risk_items: list[str]
    policy_flags: list[str]
    manual_review_reasons: list[str]
    confidence: Literal["low", "medium", "high"]
    suggested_milestones: list[str]


class PlanTaskDraft(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    definition_of_done: str = Field(min_length=10, max_length=2_000)
    criterion_ordinals: list[int] = Field(min_length=1)
    estimate_hours: int = Field(ge=1, le=40)
    dependency_titles: list[str] = Field(default_factory=list)


class PlanMilestoneDraft(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    due_offset_days: int = Field(ge=1, le=120)
    tasks: list[PlanTaskDraft] = Field(min_length=1)


class PlanDraft(BaseModel):
    milestones: list[PlanMilestoneDraft] = Field(min_length=1, max_length=20)
    risks: list[str] = Field(default_factory=list, max_length=30)


class PlanInput(BaseModel):
    project_title: str
    scope_version_id: uuid.UUID
    criterion_count: int = Field(ge=1, le=100)


class PlanRunView(ApiModel):
    id: uuid.UUID
    project_id: uuid.UUID
    scope_version_id: uuid.UUID
    agent_run_id: uuid.UUID
    status: str
    plan_snapshot: dict[str, Any]
    created_at: datetime


class DecisionRequest(BaseModel):
    decision: Literal["APPROVED", "REJECTED"]
    reason: str = Field(min_length=10, max_length=2_000)


class QACriterionResult(BaseModel):
    criterion_ordinal: int = Field(ge=1)
    passed: bool
    summary: str = Field(min_length=5, max_length=2_000)
    evidence: dict[str, Any] = Field(default_factory=dict)


class QADraft(BaseModel):
    recommendation: Literal["PASS", "CHANGES_REQUIRED"]
    criterion_results: list[QACriterionResult] = Field(min_length=1)
    summary: str = Field(min_length=10, max_length=4_000)


class QAInput(BaseModel):
    artifact_id: uuid.UUID
    artifact_kind: str
    artifact_uri: str
    artifact_content_hash: str
    acceptance_criteria: list[str] = Field(min_length=1)


class QAReviewView(ApiModel):
    id: uuid.UUID
    deliverable_id: uuid.UUID
    artifact_id: uuid.UUID
    status: str
    recommendation: str
    deterministic_evidence: dict[str, Any]
    agent_run_id: uuid.UUID | None
    created_at: datetime


class LeadReviewRequest(BaseModel):
    recommendation: Literal["RELEASE", "CHANGES_REQUIRED"]
    findings: list[str] = Field(default_factory=list, max_length=50)
    conflict_declared: bool


class ScopeChangeCreate(BaseModel):
    request_text: str = Field(min_length=10, max_length=4_000)
    changes_deliverable: bool = False
    changes_acceptance_criterion: bool = False
    adds_integration: bool = False
    adds_environment: bool = False
    exceeds_effort_bound: bool = False
    corrects_verified_defect: bool = False


class ScopeChangeView(ApiModel):
    id: uuid.UUID
    project_id: uuid.UUID
    requested_by_id: uuid.UUID
    request_text: str
    classification: str
    evidence: dict[str, Any]
    classified_by_id: uuid.UUID | None
    created_at: datetime


class CompensationShare(BaseModel):
    recipient_user_id: uuid.UUID
    amount_minor: int = Field(gt=0, le=9_000_000_000_000)


class ChangeOrderCreate(BaseModel):
    scope_change_request_id: uuid.UUID
    scope_diff: dict[str, Any]
    added_compensation_minor: int = Field(gt=0, le=9_000_000_000_000)
    added_days: int = Field(ge=0, le=365)
    compensation_shares: list[CompensationShare] = Field(min_length=1, max_length=20)


class ChangeOrderDecision(BaseModel):
    decision: Literal["ACCEPTED", "REJECTED"]
    reason: str = Field(min_length=10, max_length=2_000)


class ChangeOrderView(ApiModel):
    id: uuid.UUID
    project_id: uuid.UUID
    version: int
    state: str
    scope_diff: dict[str, Any]
    added_compensation_minor: int
    added_days: int
    created_at: datetime


class AgentRunView(ApiModel):
    id: uuid.UUID
    project_id: uuid.UUID | None
    agent_name: str
    status: str
    model_identifier: str | None
    prompt_version: str
    input_snapshot_hash: str
    output: dict[str, Any] | None
    validation_status: str
    latency_ms: int | None
    retry_count: int
    usage: dict[str, Any] | None
    correlation_id: uuid.UUID
    is_demo: bool
    created_at: datetime


class QuoteInput(BaseModel):
    student_hours_low: int = Field(ge=1, le=10_000)
    student_hours_base: int = Field(ge=1, le=10_000)
    student_hours_high: int = Field(ge=1, le=10_000)
    student_rate_minor: int = Field(gt=0, le=10_000_000)
    lead_hours: int = Field(ge=0, le=1_000)
    lead_rate_minor: int = Field(ge=0, le=10_000_000)
    platform_fee_basis_points: int = Field(ge=0, le=5_000)
    risk_multiplier_basis_points: int = Field(ge=10_000, le=15_000)
    tax_basis_points: int = Field(ge=0, le=5_000)
    currency: str = Field(pattern=r"^[A-Z]{3}$")
    revision_rounds: int = Field(ge=0, le=5)


class QuoteResult(BaseModel):
    low_minor: int
    base_minor: int
    high_minor: int
    currency: str
    line_items: dict[str, int]
    revision_rounds: int
    formula_version: str


class OfferView(ApiModel):
    id: uuid.UUID
    project_id: uuid.UUID
    recipient_user_id: uuid.UUID
    role: str
    state: str
    terms_snapshot: dict[str, Any]
    expires_at: datetime
    decided_at: datetime | None


class OfferCreate(BaseModel):
    recipient_user_id: uuid.UUID
    role: Literal["student", "technical lead"]
    role_title: str = Field(min_length=2, max_length=100)
    gross_compensation_minor: int = Field(gt=0, le=9_000_000_000_000)
    currency: str = Field(pattern=r"^[A-Z]{3}$")
    expected_hours_low: int = Field(ge=1, le=200)
    expected_hours_high: int = Field(ge=1, le=200)
    expected_weekly_hours: int = Field(ge=1, le=40)
    deadline: datetime
    revision_rounds: int = Field(ge=0, le=5)
    portfolio_terms: str = Field(min_length=5, max_length=1_000)
    expires_at: datetime
    conflict_declared: bool = False


class OfferDecisionRequest(BaseModel):
    expected_state: Literal["OFFERED"] = "OFFERED"


class CheckInCreate(BaseModel):
    progress: str = Field(min_length=1, max_length=4_000)
    next_step: str = Field(min_length=1, max_length=4_000)
    blocker: str | None = Field(default=None, max_length=4_000)
    help_needed: str | None = Field(default=None, max_length=4_000)


class DeliverableCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    artifact_kind: Literal["repository", "deployment", "document", "upload"]
    artifact_uri: HttpUrl
    commit_sha: str | None = Field(default=None, pattern=r"^[0-9a-fA-F]{7,64}$")


class PublicCredential(BaseModel):
    status: Literal["VALID", "REVOKED", "NOT_FOUND"]
    signature_valid: bool
    credential: dict[str, Any] | None
    environment_label: str | None = None


class CredentialSkillEvidence(BaseModel):
    evidence_id: uuid.UUID
    skill: str = Field(min_length=2, max_length=100)
    criterion: str = Field(min_length=2, max_length=200)
    summary: str = Field(min_length=10, max_length=1_000)


class CredentialIssueRequest(BaseModel):
    student_user_id: uuid.UUID
    contribution_summary: str = Field(min_length=20, max_length=2_000)
    skill_evidence: list[CredentialSkillEvidence] = Field(min_length=1, max_length=30)


class CredentialRevokeRequest(BaseModel):
    reason: str = Field(min_length=20, max_length=2_000)


class ExternalFundingRequest(BaseModel):
    amount_minor: int = Field(gt=0, le=9_000_000_000_000)
    currency: str = Field(pattern=r"^[A-Z]{3}$")
    evidence_reference: str = Field(min_length=5, max_length=500)
    approved_arrangement: bool


class PayoutAllocationCreate(BaseModel):
    recipient_user_id: uuid.UUID
    amount_minor: int = Field(gt=0, le=9_000_000_000_000)
    currency: str = Field(pattern=r"^[A-Z]{3}$")


class PayoutAllocationView(ApiModel):
    id: uuid.UUID
    project_id: uuid.UUID
    recipient_user_id: uuid.UUID
    amount_minor: int
    currency: str
    status: str
    approved_by_id: uuid.UUID | None
    created_at: datetime


class ExternalPayoutRequest(BaseModel):
    approved_arrangement: Literal[True]
    external_reference: str = Field(min_length=6, max_length=255)
    evidence_summary: str = Field(min_length=20, max_length=2_000)


class PayoutRecordView(ApiModel):
    id: uuid.UUID
    allocation_id: uuid.UUID
    provider_reference: str | None
    status: str
    failure_reason: str | None
    evidence_hash: str | None
    created_at: datetime


class ClientInvoiceView(ApiModel):
    id: uuid.UUID
    project_id: uuid.UUID
    project_title: str
    number: str
    amount_minor: int
    currency: str
    status: str
    environment: str
    created_at: datetime


class StudentCredentialView(ApiModel):
    id: uuid.UUID
    project_id: uuid.UUID
    project_title: str
    public_slug: str
    status: Literal["VALID", "REVOKED"]
    issued_at: datetime


class EarningsItemView(ApiModel):
    allocation_id: uuid.UUID
    project_id: uuid.UUID
    project_title: str
    amount_minor: int
    currency: str
    allocation_status: str
    payout_status: str | None
    failure_reason: str | None


class LeadReviewQueueItem(BaseModel):
    project_id: uuid.UUID
    project_title: str
    project_state: str
    latest_recommendation: str | None
    latest_reviewed_at: datetime | None


class ApprovalQueueItem(ApiModel):
    id: uuid.UUID
    project_id: uuid.UUID
    project_title: str
    subject_type: str
    subject_id: uuid.UUID
    decision: str
    reason: str
    created_at: datetime


class RiskQueueItem(ApiModel):
    id: uuid.UUID
    project_id: uuid.UUID
    project_title: str
    source: str
    summary: str
    confidence: str
    status: str
    human_decision: str | None
    created_at: datetime


class DashboardSummary(BaseModel):
    environment_label: str
    is_demo: bool
    projects_by_state: dict[str, int]
    pending_approvals: int
    failed_agent_runs: int
    dead_letter_jobs: int
    payment_exceptions: int


class DeadLetterRecoveryRequest(BaseModel):
    reason: str = Field(min_length=20, max_length=2_000)


class JobAttemptView(ApiModel):
    id: uuid.UUID
    attempt_number: int
    status: str
    started_at: datetime
    finished_at: datetime | None
    error_category: str | None
    error_message: str | None


class OperationsJobView(ApiModel):
    id: uuid.UUID
    event_type: str
    aggregate_type: str
    aggregate_id: uuid.UUID
    status: str
    attempts: int
    available_at: datetime
    last_error: str | None
    attempt_history: list[JobAttemptView]


class IntegrationStatus(BaseModel):
    provider: str
    mode: str
    configured: bool
    live_side_effects_enabled: bool
    last_sync_status: str | None = None
    last_synced_at: datetime | None = None
    last_error_category: str | None = None


NotificationCategory = Literal[
    "projects", "offers", "payments", "credentials", "appeals", "operations"
]


class NotificationView(ApiModel):
    id: uuid.UUID
    kind: str
    title: str
    body: str
    resource_path: str | None
    read_at: datetime | None
    created_at: datetime


class NotificationPreferenceUpdate(BaseModel):
    category: NotificationCategory
    enabled: bool


class NotificationPreferenceView(ApiModel):
    category: NotificationCategory
    enabled: bool


class ProviderSynchronizationView(ApiModel):
    id: uuid.UUID
    provider: str
    operation: str
    mode: str
    status: str
    resource_type: str
    resource_id: uuid.UUID | None
    correlation_id: uuid.UUID
    error_category: str | None
    details: dict[str, Any]
    checked_at: datetime


class UniversityMetrics(BaseModel):
    suppressed: bool
    minimum_cohort_size: int
    consented_cohort_size: int | None
    participating_students: int | None
    completed_projects: int | None
    credentials_issued: int | None
    verified_work_minutes: int | None
    as_of: datetime


class UniversityExportRequest(BaseModel):
    purpose: str = Field(min_length=20, max_length=2_000)


class UniversityExportView(ApiModel):
    id: uuid.UUID
    purpose: str
    status: str
    storage_key: str | None
    expires_at: datetime
    created_at: datetime


class TaskCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    definition_of_done: str = Field(min_length=10, max_length=4_000)
    milestone_id: uuid.UUID | None = None
    assignee_id: uuid.UUID | None = None
    dependency_ids: list[uuid.UUID] = Field(default_factory=list, max_length=30)
    estimate_hours: int = Field(ge=1, le=80)


class TaskView(ApiModel):
    id: uuid.UUID
    project_id: uuid.UUID
    milestone_id: uuid.UUID | None
    assignee_id: uuid.UUID | None
    title: str
    definition_of_done: str
    state: str
    dependency_ids: list[str]
    estimate_hours: int


class MilestoneView(ApiModel):
    id: uuid.UUID
    project_id: uuid.UUID
    title: str
    ordinal: int
    due_at: datetime
    status: str


class DeliverableEvidenceView(ApiModel):
    id: uuid.UUID
    title: str
    status: str
    version: int
    artifact_kind: str | None
    artifact_content_hash: str | None
    scan_status: str | None
    qa_status: str | None
    qa_recommendation: str | None
    lead_recommendation: str | None
    client_decision: str | None
    created_at: datetime


class ProjectTimelineItem(ApiModel):
    id: uuid.UUID
    previous_state: str
    new_state: str
    reason: str
    created_at: datetime


class ScopeVersionView(ApiModel):
    id: uuid.UUID
    version: int
    status: str
    snapshot: dict[str, Any]
    acceptance_criteria: list[str]
    immutable_at: datetime | None
    created_at: datetime


class QuoteLineItemView(ApiModel):
    kind: str
    description: str
    amount_minor: int


class QuoteView(ApiModel):
    id: uuid.UUID
    scope_version_id: uuid.UUID
    version: int
    currency: str
    low_minor: int
    base_minor: int
    high_minor: int
    revision_rounds: int
    formula_version: str
    status: str
    line_items: list[QuoteLineItemView]
    created_at: datetime


class StaffingCandidateView(ApiModel):
    student_profile_id: uuid.UUID
    student_user_id: uuid.UUID
    display_name: str
    score_basis_points: int
    confidence: str
    components: dict[str, int]
    explanation: str


class StaffingRunView(ApiModel):
    id: uuid.UUID
    status: str
    weights_version: str
    candidates: list[StaffingCandidateView]
    created_at: datetime


class LeadCandidateView(ApiModel):
    user_id: uuid.UUID
    display_name: str
    domains: list[str]
    available_hours: int


class ProjectOfferView(ApiModel):
    id: uuid.UUID
    recipient_user_id: uuid.UUID
    recipient_display_name: str
    role: str
    state: str
    terms_snapshot: dict[str, Any]
    expires_at: datetime
    decided_at: datetime | None


class ProjectPlanView(ApiModel):
    id: uuid.UUID
    status: str
    plan_snapshot: dict[str, Any]
    created_at: datetime


class ProjectWorkspaceView(BaseModel):
    project: ProjectView
    latest_scope: ScopeVersionView | None
    latest_quote: QuoteView | None
    latest_staffing: StaffingRunView | None
    eligible_leads: list[LeadCandidateView]
    assignment_offers: list[ProjectOfferView]
    latest_plan: ProjectPlanView | None
    milestones: list[MilestoneView]
    tasks: list[TaskView]
    deliverables: list[DeliverableEvidenceView]
    risks: list[RiskQueueItem]
    timeline: list[ProjectTimelineItem]


class TaskTransitionRequest(BaseModel):
    target: str = Field(pattern="^(BACKLOG|READY|IN_PROGRESS|BLOCKED|IN_REVIEW|DONE)$")


class AppealCreate(BaseModel):
    project_id: uuid.UUID
    decision_type: Literal["qa", "deliverable", "payout", "credential", "reputation"]
    decision_id: uuid.UUID
    decision_snapshot: dict[str, Any]


class AppealResolve(BaseModel):
    decision: Literal["UPHELD", "OVERTURNED", "PARTIALLY_OVERTURNED"]
    reason: str = Field(min_length=20, max_length=4_000)


class ReputationEventCreate(BaseModel):
    student_user_id: uuid.UUID
    project_id: uuid.UUID
    dimension: Literal["reliability", "delivered_quality", "collaboration", "verified_skill"]
    value: int = Field(ge=-100, le=100)
    evidence_type: Literal[
        "client_acceptance", "lead_review", "appeal_resolution", "coordinator_investigation"
    ]
    evidence_id: uuid.UUID


class LearningContentSection(BaseModel):
    title: str
    body: str


class LearningModuleView(ApiModel):
    id: uuid.UUID
    ordinal: int
    title: str
    summary: str
    estimated_minutes: int
    content_sections: list[LearningContentSection]
    exercise_brief: str
    completion_evidence: str
    completed: bool


class LearningPathView(ApiModel):
    id: uuid.UUID
    slug: str
    title: str
    summary: str
    level: str
    estimated_hours: int
    skill_outcomes: list[str]
    prerequisites: list[str]
    modules: list[LearningModuleView]
    enrolled: bool
    progress_percent: int
    status: str | None


class LearningModuleCompleteRequest(BaseModel):
    evidence_summary: str = Field(min_length=20, max_length=2_000)


class ProposalPlanStep(BaseModel):
    milestone: str = Field(min_length=3, max_length=120)
    outcome: str = Field(min_length=10, max_length=500)


class ProposalEvidence(BaseModel):
    title: str = Field(min_length=3, max_length=120)
    url: HttpUrl
    relevance: str = Field(min_length=10, max_length=500)


class StudentProposalCreate(BaseModel):
    cover_note: str = Field(min_length=40, max_length=2_000)
    approach: str = Field(min_length=80, max_length=4_000)
    delivery_plan: list[ProposalPlanStep] = Field(min_length=1, max_length=8)
    relevant_evidence: list[ProposalEvidence] = Field(min_length=1, max_length=8)
    proposed_amount_minor: int = Field(gt=0, le=9_000_000_000_000)
    currency: str = Field(pattern=r"^[A-Z]{3}$")
    estimated_days: int = Field(ge=1, le=120)
    availability_hours_per_week: int = Field(ge=1, le=40)


class StudentProposalView(ApiModel):
    id: uuid.UUID
    opportunity_id: uuid.UUID
    student_user_id: uuid.UUID
    student_display_name: str
    cover_note: str
    approach: str
    delivery_plan: list[ProposalPlanStep]
    relevant_evidence: list[ProposalEvidence]
    proposed_amount_minor: int
    currency: str
    estimated_days: int
    availability_hours_per_week: int
    state: str
    decision_reason: str | None
    decided_at: datetime | None
    created_at: datetime


class OpportunityPublishRequest(BaseModel):
    project_id: uuid.UUID
    headline: str = Field(min_length=5, max_length=200)
    brief: str = Field(min_length=80, max_length=8_000)
    required_skills: list[str] = Field(min_length=1, max_length=20)
    nice_to_have_skills: list[str] = Field(default_factory=list, max_length=20)
    deliverables: list[str] = Field(min_length=1, max_length=20)
    proposal_requirements: list[str] = Field(min_length=1, max_length=20)
    estimated_hours_low: int = Field(ge=1, le=200)
    estimated_hours_high: int = Field(ge=1, le=200)
    budget_minor: int = Field(gt=0, le=9_000_000_000_000)
    currency: str = Field(pattern=r"^[A-Z]{3}$")
    deadline: datetime
    supervision_level: Literal["guided", "supported", "independent"]
    max_proposals: int = Field(default=20, ge=1, le=100)


class OpportunityView(ApiModel):
    id: uuid.UUID
    project_id: uuid.UUID
    employer_name: str
    headline: str
    brief: str
    required_skills: list[str]
    nice_to_have_skills: list[str]
    deliverables: list[str]
    proposal_requirements: list[str]
    estimated_hours_low: int
    estimated_hours_high: int
    budget_minor: int
    currency: str
    deadline: datetime
    supervision_level: str
    status: str
    proposal_count: int
    my_proposal: StudentProposalView | None
    created_at: datetime


class EmployerOpportunityView(OpportunityView):
    proposals: list[StudentProposalView]


class ProposalDecisionRequest(BaseModel):
    decision: Literal["ACCEPTED", "REJECTED"]
    reason: str = Field(min_length=20, max_length=2_000)
