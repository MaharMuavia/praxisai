import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class InternshipSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ProgramSummary(InternshipSchema):
    id: uuid.UUID
    slug: str
    name: str
    public_description: str
    status: str
    duration_weeks: int
    default_timezone: str
    is_demo: bool


class TrackSummary(InternshipSchema):
    id: uuid.UUID
    name: str
    slug: str
    version_id: uuid.UUID
    version: int
    title: str
    summary: str
    skill_outcomes: list[str]
    expected_weekly_hours: int


class ProgramDetail(ProgramSummary):
    cohorts: list["CohortSummary"]
    tracks: list[TrackSummary]


class CohortSummary(InternshipSchema):
    id: uuid.UUID
    name: str
    slug: str
    timezone: str
    starts_at: datetime
    ends_at: datetime
    application_deadline: datetime | None
    status: str
    capacity: int
    is_demo: bool


class SignupRequest(BaseModel):
    id_token: str = Field(min_length=20, max_length=16_000)
    cohort_id: uuid.UUID
    consent_version: str = Field(min_length=1, max_length=30)


class SignupResponse(InternshipSchema):
    status: Literal["CREATED", "CHECK_EMAIL"]
    message: str
    application_id: uuid.UUID | None = None


class StartApplicationRequest(BaseModel):
    program_id: uuid.UUID
    cohort_id: uuid.UUID
    consent_version: str = Field(min_length=1, max_length=30)


class ApplicationUpdate(BaseModel):
    version: int = Field(ge=1)
    primary_track_id: uuid.UUID | None = None
    secondary_track_id: uuid.UUID | None = None
    education_status: str = Field(default="", max_length=80)
    university_id: uuid.UUID | None = None
    degree_program: str = Field(default="", max_length=180)
    semester_status: str = Field(default="", max_length=180)
    country: str = Field(default="", min_length=2, max_length=2)
    timezone: str = Field(default="UTC", max_length=80)
    weekly_availability_hours: int | None = Field(default=None, ge=1, le=80)
    technical_background: str = Field(default="", max_length=4_000)
    motivation: str = Field(default="", max_length=4_000)
    portfolio_url: HttpUrl | None = None
    github_url: HttpUrl | None = None
    linkedin_url: HttpUrl | None = None
    accessibility_requirements: str | None = Field(default=None, max_length=2_000)


class ApplicationView(InternshipSchema):
    id: uuid.UUID
    program_id: uuid.UUID
    cohort_id: uuid.UUID
    applicant_user_id: uuid.UUID
    status: str
    version: int
    primary_track_id: uuid.UUID | None
    secondary_track_id: uuid.UUID | None
    education_status: str
    degree_program: str
    country: str
    timezone: str
    weekly_availability_hours: int | None
    technical_background: str
    motivation: str
    portfolio_url: str | None
    github_url: str | None
    linkedin_url: str | None
    submitted_at: datetime | None
    decision_at: datetime | None
    decision_reason: str | None
    is_demo: bool


class ApplicationSubmitRequest(BaseModel):
    version: int = Field(ge=1)
    consent_version: str = Field(min_length=1, max_length=30)


class TimelineItem(InternshipSchema):
    label: str
    state: str
    starts_at: datetime | None = None
    ends_at: datetime | None = None


class DashboardView(InternshipSchema):
    enrollment_id: uuid.UUID | None
    program_name: str | None
    cohort_name: str | None
    track: TrackSummary | None
    enrollment_status: str | None
    certificate_eligibility: str | None
    completed_units: int
    required_units: int
    passed_assignments: int
    required_assignments: int
    progress_percent: int
    timeline: list[TimelineItem]
    is_demo: bool


class ResourceView(InternshipSchema):
    title: str
    resource_type: str
    url: HttpUrl | None = None
    duration_minutes: int | None = None
    accessibility_notes: str | None = None


class UnitView(InternshipSchema):
    id: uuid.UUID
    week_id: uuid.UUID
    ordinal: int
    unit_type: str
    title: str
    summary: str
    objectives: list[str]
    resources: list[dict[str, Any]]
    practical_exercise: str
    completion_rule: dict[str, Any]
    prerequisites: list[str]
    release_at: datetime | None
    deadline: datetime | None
    is_required: bool
    completed: bool


class WeekView(InternshipSchema):
    id: uuid.UUID
    week_number: int
    title: str
    summary: str
    starts_at: datetime
    ends_at: datetime
    required_unit_count: int
    required_assignment_count: int
    unlocked: bool
    units: list[UnitView]


class CurriculumView(InternshipSchema):
    track: TrackSummary
    weeks: list[WeekView]


class UnitCompletionRequest(BaseModel):
    evidence_summary: str = Field(min_length=20, max_length=2_000)
    evidence_url: HttpUrl | None = None


class AssignmentView(InternshipSchema):
    id: uuid.UUID
    title: str
    summary: str
    problem_statement: str
    objectives: list[str]
    deliverables: list[str]
    acceptance_criteria: list[str]
    required_artifact_types: list[dict[str, Any]]
    rubric: list[dict[str, Any]]
    pass_score: int
    state: str
    release_at: datetime
    due_at: datetime
    submitted_at: datetime | None
    attempt_count: int
    current_submission_id: uuid.UUID | None
    is_late: bool


class SubmissionDraftRequest(BaseModel):
    links: dict[str, HttpUrl] = Field(default_factory=dict)
    text_fields: dict[str, str] = Field(default_factory=dict)
    artifact_upload_ids: list[str] = Field(default_factory=list, max_length=30)


class UploadInitiateRequest(BaseModel):
    assignment_id: uuid.UUID
    artifact_type: str = Field(min_length=2, max_length=50)
    filename: str = Field(min_length=1, max_length=255)
    content_type: str = Field(min_length=3, max_length=120)
    size_bytes: int = Field(gt=0, le=250 * 1024 * 1024)
    sha256: str | None = Field(default=None, pattern=r"^[a-fA-F0-9]{64}$")


class UploadView(InternshipSchema):
    upload_id: str
    artifact_type: str
    filename: str
    state: str
    expires_at: datetime
    upload_url: str


class UploadCompleteRequest(BaseModel):
    sha256: str = Field(pattern=r"^[a-fA-F0-9]{64}$")


class SubmissionView(InternshipSchema):
    id: uuid.UUID
    student_assignment_id: uuid.UUID
    state: str
    version: int
    links: dict[str, str]
    text_fields: dict[str, str]
    artifact_upload_ids: list[str]
    artifact_snapshot: list[dict[str, Any]]
    canonical_hash: str | None
    submitted_at: datetime | None
    deadline_status: str | None
    previous_submission_id: uuid.UUID | None
    change_summary: str | None


class FinalizeSubmissionRequest(BaseModel):
    confirm: bool
    version: int = Field(ge=1)


class ResubmissionRequest(BaseModel):
    change_summary: str = Field(min_length=20, max_length=4_000)


class ReviewFinalizeRequest(BaseModel):
    version: int = Field(ge=1)
    scores: list[dict[str, Any]] = Field(min_length=1, max_length=50)
    student_feedback: str = Field(min_length=20, max_length=4_000)
    private_notes: str | None = Field(default=None, max_length=4_000)
    decision: Literal["PASS", "CHANGES_REQUESTED", "FAIL"]
    conflict_declared: bool = False


class ReviewAssignRequest(BaseModel):
    reviewer_id: uuid.UUID


class FeedbackView(InternshipSchema):
    review_id: uuid.UUID
    assignment_id: uuid.UUID
    submission_id: uuid.UUID
    decision: str
    weighted_total: int
    student_feedback: str
    finalized_at: datetime


class CertificateEligibilityView(InternshipSchema):
    enrollment_id: uuid.UUID | None
    state: str
    reason: str
    certificate_id: uuid.UUID | None
    public_slug: str | None


class PublicCertificateView(InternshipSchema):
    state: str
    public_slug: str
    payload: dict[str, Any]


class ApplicationDecisionRequest(BaseModel):
    decision: Literal["ACCEPTED", "WAITLISTED", "REJECTED"]
    reason: str = Field(min_length=10, max_length=2_000)
    track_version_id: uuid.UUID | None = None
    expected_version: int = Field(ge=1)


class OperationsApplicationView(ApplicationView):
    applicant_display_name: str
    applicant_email: str


class ReviewQueueItem(InternshipSchema):
    review_id: uuid.UUID
    assignment_id: uuid.UUID
    submission_id: uuid.UUID
    student_display_name: str
    assignment_title: str
    status: str
    version: int


class CompletionDecisionRequest(BaseModel):
    decision: Literal["APPROVED", "REJECTED"]
    reason: str = Field(min_length=10, max_length=2_000)


class IssueCertificateRequest(BaseModel):
    confirm: bool


ProgramDetail.model_rebuild()
