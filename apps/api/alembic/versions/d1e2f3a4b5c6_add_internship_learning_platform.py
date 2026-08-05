"""Add the internship learning and project execution domain.

This migration is intentionally explicit.  The internship tables are part of
the durable database contract and must not be created from ORM metadata at
runtime or during an Alembic upgrade.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d1e2f3a4b5c6"
down_revision: str | None = "c9d4e5f6a701"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _common() -> tuple[sa.Column[object], ...]:
    return (
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def upgrade() -> None:
    op.create_table(
        "internship_programs",
        *_common(),
        sa.Column("slug", sa.String(120), nullable=False),
        sa.Column("name", sa.String(220), nullable=False),
        sa.Column("public_description", sa.Text(), nullable=False),
        sa.Column("internal_description", sa.Text(), nullable=False, server_default=""),
        sa.Column("status", sa.String(30), nullable=False, server_default="DRAFT"),
        sa.Column("default_timezone", sa.String(80), nullable=False, server_default="UTC"),
        sa.Column("duration_weeks", sa.Integer(), nullable=False),
        sa.Column("application_opens_at", sa.DateTime(timezone=True)),
        sa.Column("application_closes_at", sa.DateTime(timezone=True)),
        sa.Column("minimum_age", sa.Integer()),
        sa.Column("university_email_policy", sa.String(30), nullable=False, server_default="REVIEW"),
        sa.Column("personal_email_exception_policy", sa.String(30), nullable=False, server_default="REVIEW"),
        sa.Column("completion_policy_version", sa.String(30), nullable=False, server_default="1.0"),
        sa.Column("certificate_policy_version", sa.String(30), nullable=False, server_default="1.0"),
        sa.Column("is_demo", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_unique_constraint(
        "uq_internship_programs_slug", "internship_programs", ["slug"]
    )
    op.create_check_constraint(
        "ck_internship_programs_duration_positive", "internship_programs", "duration_weeks > 0"
    )
    op.create_index("ix_internship_programs_slug", "internship_programs", ["slug"])
    op.create_index("ix_internship_programs_status", "internship_programs", ["status"])

    op.create_table(
        "internship_tracks",
        *_common(),
        sa.Column("slug", sa.String(120), nullable=False),
        sa.Column("name", sa.String(180), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("is_demo", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.UniqueConstraint("slug", name="uq_internship_tracks_slug"),
    )
    op.create_index("ix_internship_tracks_slug", "internship_tracks", ["slug"])

    op.create_table(
        "internship_track_versions",
        *_common(),
        sa.Column("track_id", sa.Uuid(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("prerequisites", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("skill_outcomes", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("expected_weekly_hours", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("status", sa.String(30), nullable=False, server_default="DRAFT"),
        sa.Column("published_at", sa.DateTime(timezone=True)),
        sa.Column("published_by_id", sa.Uuid()),
        sa.Column("learning_path_id", sa.Uuid()),
        sa.Column("is_demo", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.ForeignKeyConstraint(["track_id"], ["internship_tracks.id"], name="fk_track_versions_track"),
        sa.ForeignKeyConstraint(["published_by_id"], ["users.id"], name="fk_track_versions_publisher"),
        sa.ForeignKeyConstraint(["learning_path_id"], ["learning_paths.id"], name="fk_track_versions_learning_path"),
        sa.UniqueConstraint("track_id", "version", name="uq_internship_track_versions_track_version"),
        sa.CheckConstraint("version > 0", name="ck_internship_track_versions_version_positive"),
        sa.CheckConstraint("expected_weekly_hours > 0", name="ck_internship_track_versions_hours_positive"),
    )
    op.create_index("ix_internship_track_versions_track_id", "internship_track_versions", ["track_id"])
    op.create_index("ix_internship_track_versions_status", "internship_track_versions", ["status"])

    op.create_table(
        "internship_cohorts",
        *_common(),
        sa.Column("program_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(220), nullable=False),
        sa.Column("slug", sa.String(120), nullable=False),
        sa.Column("timezone", sa.String(80), nullable=False, server_default="UTC"),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("capacity", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="DRAFT"),
        sa.Column("application_deadline", sa.DateTime(timezone=True)),
        sa.Column("enrollment_deadline", sa.DateTime(timezone=True)),
        sa.Column("late_policy", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("resubmission_policy", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("certificate_policy", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("coordinator_id", sa.Uuid()),
        sa.Column("is_demo", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.ForeignKeyConstraint(["program_id"], ["internship_programs.id"], name="fk_internship_cohorts_program"),
        sa.ForeignKeyConstraint(["coordinator_id"], ["users.id"], name="fk_internship_cohorts_coordinator"),
        sa.UniqueConstraint("program_id", "slug", name="uq_internship_cohorts_program_slug"),
        sa.CheckConstraint("capacity > 0", name="ck_internship_cohorts_capacity_positive"),
        sa.CheckConstraint("ends_at > starts_at", name="ck_internship_cohorts_dates_valid"),
    )
    op.create_index("ix_internship_cohorts_program_id", "internship_cohorts", ["program_id"])
    op.create_index("ix_internship_cohorts_slug", "internship_cohorts", ["slug"])
    op.create_index("ix_internship_cohorts_status", "internship_cohorts", ["status"])

    op.create_table(
        "internship_cohort_tracks",
        *_common(),
        sa.Column("cohort_id", sa.Uuid(), nullable=False),
        sa.Column("track_version_id", sa.Uuid(), nullable=False),
        sa.Column("capacity", sa.Integer(), nullable=False),
        sa.Column("reviewer_pool", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("instructor_id", sa.Uuid()),
        sa.ForeignKeyConstraint(["cohort_id"], ["internship_cohorts.id"], name="fk_cohort_tracks_cohort"),
        sa.ForeignKeyConstraint(["track_version_id"], ["internship_track_versions.id"], name="fk_cohort_tracks_track_version"),
        sa.ForeignKeyConstraint(["instructor_id"], ["users.id"], name="fk_cohort_tracks_instructor"),
        sa.UniqueConstraint("cohort_id", "track_version_id", name="uq_internship_cohort_tracks_cohort_version"),
        sa.CheckConstraint("capacity > 0", name="ck_internship_cohort_tracks_capacity_positive"),
    )
    op.create_index("ix_internship_cohort_tracks_cohort_id", "internship_cohort_tracks", ["cohort_id"])
    op.create_index("ix_internship_cohort_tracks_track_version_id", "internship_cohort_tracks", ["track_version_id"])

    op.create_table(
        "university_email_domains",
        *_common(),
        sa.Column("university_id", sa.Uuid(), nullable=False),
        sa.Column("domain", sa.String(255), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="PENDING"),
        sa.Column("allow_subdomains", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("verification_method", sa.String(40), nullable=False, server_default="manual"),
        sa.Column("verified_at", sa.DateTime(timezone=True)),
        sa.Column("verified_by_id", sa.Uuid()),
        sa.ForeignKeyConstraint(["university_id"], ["universities.id"], name="fk_university_email_domains_university"),
        sa.ForeignKeyConstraint(["verified_by_id"], ["users.id"], name="fk_university_email_domains_verifier"),
        sa.UniqueConstraint("university_id", "domain", name="uq_university_email_domains_university_domain"),
    )
    op.create_index("ix_university_email_domains_university_id", "university_email_domains", ["university_id"])
    op.create_index("ix_university_email_domains_domain", "university_email_domains", ["domain"])
    op.create_index("ix_university_email_domains_status", "university_email_domains", ["status"])

    op.create_table(
        "allowed_student_emails",
        *_common(),
        sa.Column("cohort_id", sa.Uuid(), nullable=False),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="ACTIVE"),
        sa.Column("invitation_source", sa.String(120)),
        sa.Column("expires_at", sa.DateTime(timezone=True)),
        sa.Column("accepted_at", sa.DateTime(timezone=True)),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(["cohort_id"], ["internship_cohorts.id"], name="fk_allowed_student_emails_cohort"),
        sa.UniqueConstraint("cohort_id", "email", name="uq_allowed_student_emails_cohort_email"),
    )
    op.create_index("ix_allowed_student_emails_cohort_id", "allowed_student_emails", ["cohort_id"])
    op.create_index("ix_allowed_student_emails_email", "allowed_student_emails", ["email"])
    op.create_index("ix_allowed_student_emails_status", "allowed_student_emails", ["status"])

    op.create_table(
        "internship_applications",
        *_common(),
        sa.Column("applicant_user_id", sa.Uuid(), nullable=False),
        sa.Column("program_id", sa.Uuid(), nullable=False),
        sa.Column("cohort_id", sa.Uuid(), nullable=False),
        sa.Column("primary_track_id", sa.Uuid()),
        sa.Column("secondary_track_id", sa.Uuid()),
        sa.Column("education_status", sa.String(80), nullable=False, server_default=""),
        sa.Column("university_id", sa.Uuid()),
        sa.Column("degree_program", sa.String(180), nullable=False, server_default=""),
        sa.Column("semester_status", sa.String(180), nullable=False, server_default=""),
        sa.Column("country", sa.String(2), nullable=False, server_default=""),
        sa.Column("timezone", sa.String(80), nullable=False, server_default="UTC"),
        sa.Column("weekly_availability_hours", sa.Integer()),
        sa.Column("technical_background", sa.Text(), nullable=False, server_default=""),
        sa.Column("motivation", sa.Text(), nullable=False, server_default=""),
        sa.Column("portfolio_url", sa.String(500)),
        sa.Column("github_url", sa.String(500)),
        sa.Column("linkedin_url", sa.String(500)),
        sa.Column("accessibility_requirements", sa.Text()),
        sa.Column("email_verification_evidence", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("consent_snapshot", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("status", sa.String(40), nullable=False, server_default="DRAFT"),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("submitted_at", sa.DateTime(timezone=True)),
        sa.Column("decision_at", sa.DateTime(timezone=True)),
        sa.Column("decision_reason", sa.Text()),
        sa.Column("reviewer_id", sa.Uuid()),
        sa.Column("correlation_id", sa.Uuid(), nullable=False),
        sa.Column("submit_idempotency_key", sa.String(128)),
        sa.ForeignKeyConstraint(["applicant_user_id"], ["users.id"], name="fk_internship_applications_applicant"),
        sa.ForeignKeyConstraint(["program_id"], ["internship_programs.id"], name="fk_internship_applications_program"),
        sa.ForeignKeyConstraint(["cohort_id"], ["internship_cohorts.id"], name="fk_internship_applications_cohort"),
        sa.ForeignKeyConstraint(["primary_track_id"], ["internship_tracks.id"], name="fk_internship_applications_primary_track"),
        sa.ForeignKeyConstraint(["secondary_track_id"], ["internship_tracks.id"], name="fk_internship_applications_secondary_track"),
        sa.ForeignKeyConstraint(["university_id"], ["universities.id"], name="fk_internship_applications_university"),
        sa.ForeignKeyConstraint(["reviewer_id"], ["users.id"], name="fk_internship_applications_reviewer"),
        sa.UniqueConstraint("applicant_user_id", "cohort_id", name="uq_internship_applications_applicant_cohort"),
        sa.UniqueConstraint("submit_idempotency_key", name="uq_internship_applications_submit_key"),
        sa.CheckConstraint("version > 0", name="ck_internship_applications_version_positive"),
        sa.CheckConstraint("weekly_availability_hours IS NULL OR weekly_availability_hours > 0", name="ck_internship_applications_hours_positive"),
    )
    op.create_index("ix_internship_applications_applicant_user_id", "internship_applications", ["applicant_user_id"])
    op.create_index("ix_internship_applications_program_id", "internship_applications", ["program_id"])
    op.create_index("ix_internship_applications_cohort_id", "internship_applications", ["cohort_id"])
    op.create_index("ix_internship_applications_status", "internship_applications", ["status"])
    op.create_index("ix_internship_applications_correlation_id", "internship_applications", ["correlation_id"])

    op.create_table(
        "internship_cohort_enrollments",
        *_common(),
        sa.Column("cohort_id", sa.Uuid(), nullable=False),
        sa.Column("student_user_id", sa.Uuid(), nullable=False),
        sa.Column("track_version_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="INVITED"),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("termination_reason", sa.Text()),
        sa.Column("progress_snapshot", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("certificate_eligibility", sa.String(30), nullable=False, server_default="NOT_ELIGIBLE"),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.ForeignKeyConstraint(["cohort_id"], ["internship_cohorts.id"], name="fk_internship_enrollments_cohort"),
        sa.ForeignKeyConstraint(["student_user_id"], ["users.id"], name="fk_internship_enrollments_student"),
        sa.ForeignKeyConstraint(["track_version_id"], ["internship_track_versions.id"], name="fk_internship_enrollments_track_version"),
        sa.UniqueConstraint("cohort_id", "student_user_id", name="uq_internship_enrollments_cohort_student"),
        sa.CheckConstraint("version > 0", name="ck_internship_enrollments_version_positive"),
    )
    op.create_index("ix_internship_cohort_enrollments_cohort_id", "internship_cohort_enrollments", ["cohort_id"])
    op.create_index("ix_internship_cohort_enrollments_student_user_id", "internship_cohort_enrollments", ["student_user_id"])
    op.create_index("ix_internship_cohort_enrollments_track_version_id", "internship_cohort_enrollments", ["track_version_id"])
    op.create_index("ix_internship_cohort_enrollments_status", "internship_cohort_enrollments", ["status"])

    op.create_table(
        "internship_phases",
        *_common(),
        sa.Column("cohort_track_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(180), nullable=False),
        sa.Column("phase_type", sa.String(30), nullable=False),
        sa.Column("ordinal", sa.Integer(), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completion_requirement", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.ForeignKeyConstraint(["cohort_track_id"], ["internship_cohort_tracks.id"], name="fk_internship_phases_cohort_track"),
        sa.UniqueConstraint("cohort_track_id", "ordinal", name="uq_internship_phases_cohort_track_ordinal"),
        sa.CheckConstraint("ordinal > 0", name="ck_internship_phases_ordinal_positive"),
        sa.CheckConstraint("ends_at > starts_at", name="ck_internship_phases_dates_valid"),
    )
    op.create_index("ix_internship_phases_cohort_track_id", "internship_phases", ["cohort_track_id"])

    op.create_table(
        "internship_weeks",
        *_common(),
        sa.Column("phase_id", sa.Uuid(), nullable=False),
        sa.Column("week_number", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(180), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("unlock_policy", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("required_unit_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("required_assignment_count", sa.Integer(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["phase_id"], ["internship_phases.id"], name="fk_internship_weeks_phase"),
        sa.UniqueConstraint("phase_id", "week_number", name="uq_internship_weeks_phase_number"),
        sa.CheckConstraint("week_number > 0", name="ck_internship_weeks_number_positive"),
        sa.CheckConstraint("required_unit_count >= 0 AND required_assignment_count >= 0", name="ck_internship_weeks_requirements_nonnegative"),
        sa.CheckConstraint("ends_at > starts_at", name="ck_internship_weeks_dates_valid"),
    )
    op.create_index("ix_internship_weeks_phase_id", "internship_weeks", ["phase_id"])

    op.create_table(
        "internship_units",
        *_common(),
        sa.Column("week_id", sa.Uuid(), nullable=False),
        sa.Column("ordinal", sa.Integer(), nullable=False),
        sa.Column("unit_type", sa.String(30), nullable=False),
        sa.Column("title", sa.String(220), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("objectives", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("resources", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("practical_exercise", sa.Text(), nullable=False, server_default=""),
        sa.Column("completion_rule", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("prerequisites", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("release_at", sa.DateTime(timezone=True)),
        sa.Column("deadline", sa.DateTime(timezone=True)),
        sa.Column("is_required", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("is_demo", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.ForeignKeyConstraint(["week_id"], ["internship_weeks.id"], name="fk_internship_units_week"),
        sa.UniqueConstraint("week_id", "ordinal", "version", name="uq_internship_units_week_ordinal_version"),
        sa.CheckConstraint("ordinal > 0 AND version > 0", name="ck_internship_units_positive_order_version"),
    )
    op.create_index("ix_internship_units_week_id", "internship_units", ["week_id"])

    op.create_table(
        "internship_unit_completions",
        *_common(),
        sa.Column("enrollment_id", sa.Uuid(), nullable=False),
        sa.Column("unit_id", sa.Uuid(), nullable=False),
        sa.Column("evidence", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("approved_by_id", sa.Uuid()),
        sa.ForeignKeyConstraint(["enrollment_id"], ["internship_cohort_enrollments.id"], name="fk_unit_completions_enrollment"),
        sa.ForeignKeyConstraint(["unit_id"], ["internship_units.id"], name="fk_unit_completions_unit"),
        sa.ForeignKeyConstraint(["approved_by_id"], ["users.id"], name="fk_unit_completions_approver"),
        sa.UniqueConstraint("enrollment_id", "unit_id", name="uq_internship_unit_completions_enrollment_unit"),
    )
    op.create_index("ix_internship_unit_completions_enrollment_id", "internship_unit_completions", ["enrollment_id"])
    op.create_index("ix_internship_unit_completions_unit_id", "internship_unit_completions", ["unit_id"])

    op.create_table(
        "internship_assignment_templates",
        *_common(),
        sa.Column("track_version_id", sa.Uuid(), nullable=False),
        sa.Column("week_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(220), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("problem_statement", sa.Text(), nullable=False),
        sa.Column("objectives", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("required_skills", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("estimated_effort_hours", sa.Integer(), nullable=False),
        sa.Column("starter_resources", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("constraints", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("deliverables", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("acceptance_criteria", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("required_artifact_types", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("rubric", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("maximum_score", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("pass_score", sa.Integer(), nullable=False, server_default="70"),
        sa.Column("late_policy", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("resubmission_policy", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("is_demo", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.ForeignKeyConstraint(["track_version_id"], ["internship_track_versions.id"], name="fk_assignment_templates_track_version"),
        sa.ForeignKeyConstraint(["week_id"], ["internship_weeks.id"], name="fk_assignment_templates_week"),
        sa.UniqueConstraint("track_version_id", "version", "title", name="uq_assignment_templates_track_version_version_title"),
        sa.CheckConstraint("estimated_effort_hours > 0 AND version > 0", name="ck_assignment_templates_positive_effort_version"),
        sa.CheckConstraint("maximum_score > 0 AND pass_score > 0 AND pass_score <= maximum_score", name="ck_assignment_templates_scores_valid"),
    )
    op.create_index("ix_internship_assignment_templates_track_version_id", "internship_assignment_templates", ["track_version_id"])
    op.create_index("ix_internship_assignment_templates_week_id", "internship_assignment_templates", ["week_id"])

    op.create_table(
        "internship_cohort_assignments",
        *_common(),
        sa.Column("template_id", sa.Uuid(), nullable=False),
        sa.Column("cohort_track_id", sa.Uuid(), nullable=False),
        sa.Column("release_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deadline", sa.DateTime(timezone=True), nullable=False),
        sa.Column("grace_period_minutes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("review_deadline", sa.DateTime(timezone=True)),
        sa.Column("status", sa.String(30), nullable=False, server_default="DRAFT"),
        sa.Column("reviewer_pool", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("publish_idempotency_key", sa.String(128)),
        sa.ForeignKeyConstraint(["template_id"], ["internship_assignment_templates.id"], name="fk_cohort_assignments_template"),
        sa.ForeignKeyConstraint(["cohort_track_id"], ["internship_cohort_tracks.id"], name="fk_cohort_assignments_cohort_track"),
        sa.UniqueConstraint("cohort_track_id", "template_id", name="uq_internship_cohort_assignments_cohort_template"),
        sa.UniqueConstraint("publish_idempotency_key", name="uq_internship_cohort_assignments_publish_key"),
        sa.CheckConstraint("grace_period_minutes >= 0", name="ck_cohort_assignments_grace_nonnegative"),
        sa.CheckConstraint("deadline >= release_at", name="ck_cohort_assignments_dates_valid"),
    )
    op.create_index("ix_internship_cohort_assignments_template_id", "internship_cohort_assignments", ["template_id"])
    op.create_index("ix_internship_cohort_assignments_cohort_track_id", "internship_cohort_assignments", ["cohort_track_id"])
    op.create_index("ix_internship_cohort_assignments_status", "internship_cohort_assignments", ["status"])

    op.create_table(
        "internship_student_assignments",
        *_common(),
        sa.Column("cohort_assignment_id", sa.Uuid(), nullable=False),
        sa.Column("student_user_id", sa.Uuid(), nullable=False),
        sa.Column("state", sa.String(30), nullable=False, server_default="LOCKED"),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("due_at", sa.DateTime(timezone=True)),
        sa.Column("submitted_at", sa.DateTime(timezone=True)),
        sa.Column("current_submission_id", sa.Uuid()),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("extension_state", sa.String(30), nullable=False, server_default="NONE"),
        sa.Column("final_result", sa.String(30)),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.ForeignKeyConstraint(["cohort_assignment_id"], ["internship_cohort_assignments.id"], name="fk_student_assignments_cohort_assignment"),
        sa.ForeignKeyConstraint(["student_user_id"], ["users.id"], name="fk_student_assignments_student"),
        sa.UniqueConstraint("cohort_assignment_id", "student_user_id", name="uq_internship_student_assignments_assignment_student"),
        sa.CheckConstraint("attempt_count >= 0 AND version > 0", name="ck_student_assignments_counters_valid"),
    )
    op.create_index("ix_internship_student_assignments_cohort_assignment_id", "internship_student_assignments", ["cohort_assignment_id"])
    op.create_index("ix_internship_student_assignments_student_user_id", "internship_student_assignments", ["student_user_id"])
    op.create_index("ix_internship_student_assignments_state", "internship_student_assignments", ["state"])
    op.create_index("ix_internship_student_assignments_current_submission_id", "internship_student_assignments", ["current_submission_id"])

    op.create_table(
        "internship_uploads",
        *_common(),
        sa.Column("upload_id", sa.String(80), nullable=False),
        sa.Column("owner_user_id", sa.Uuid(), nullable=False),
        sa.Column("student_assignment_id", sa.Uuid(), nullable=False),
        sa.Column("artifact_type", sa.String(50), nullable=False),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("content_type", sa.String(120), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("sha256", sa.String(64)),
        sa.Column("storage_key", sa.String(500), nullable=False),
        sa.Column("state", sa.String(30), nullable=False, server_default="INITIATED"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("scan_message", sa.String(500)),
        sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"], name="fk_internship_uploads_owner"),
        sa.ForeignKeyConstraint(["student_assignment_id"], ["internship_student_assignments.id"], name="fk_internship_uploads_assignment"),
        sa.UniqueConstraint("upload_id", name="uq_internship_uploads_upload_id"),
        sa.CheckConstraint("size_bytes > 0", name="ck_internship_uploads_size_positive"),
    )
    op.create_index("ix_internship_uploads_upload_id", "internship_uploads", ["upload_id"])
    op.create_index("ix_internship_uploads_owner_user_id", "internship_uploads", ["owner_user_id"])
    op.create_index("ix_internship_uploads_student_assignment_id", "internship_uploads", ["student_assignment_id"])
    op.create_index("ix_internship_uploads_state", "internship_uploads", ["state"])

    op.create_table(
        "internship_submissions",
        *_common(),
        sa.Column("student_assignment_id", sa.Uuid(), nullable=False),
        sa.Column("student_user_id", sa.Uuid(), nullable=False),
        sa.Column("state", sa.String(30), nullable=False, server_default="DRAFT"),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("links", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("text_fields", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("artifact_upload_ids", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("artifact_snapshot", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("canonical_hash", sa.String(64)),
        sa.Column("rubric_version", sa.Integer()),
        sa.Column("submitted_at", sa.DateTime(timezone=True)),
        sa.Column("deadline_status", sa.String(20)),
        sa.Column("correlation_id", sa.Uuid(), nullable=False),
        sa.Column("finalize_idempotency_key", sa.String(128)),
        sa.Column("previous_submission_id", sa.Uuid()),
        sa.Column("change_summary", sa.Text()),
        sa.ForeignKeyConstraint(["student_assignment_id"], ["internship_student_assignments.id"], name="fk_internship_submissions_assignment"),
        sa.ForeignKeyConstraint(["student_user_id"], ["users.id"], name="fk_internship_submissions_student"),
        sa.ForeignKeyConstraint(["previous_submission_id"], ["internship_submissions.id"], name="fk_internship_submissions_previous"),
        sa.UniqueConstraint("student_assignment_id", "version", name="uq_internship_submissions_assignment_version"),
        sa.UniqueConstraint("finalize_idempotency_key", name="uq_internship_submissions_finalize_key"),
        sa.CheckConstraint("version > 0", name="ck_internship_submissions_version_positive"),
    )
    op.create_index("ix_internship_submissions_student_assignment_id", "internship_submissions", ["student_assignment_id"])
    op.create_index("ix_internship_submissions_student_user_id", "internship_submissions", ["student_user_id"])
    op.create_index("ix_internship_submissions_state", "internship_submissions", ["state"])
    op.create_index("ix_internship_submissions_canonical_hash", "internship_submissions", ["canonical_hash"])
    op.create_index("ix_internship_submissions_correlation_id", "internship_submissions", ["correlation_id"])
    op.create_index("ix_internship_submissions_previous_submission_id", "internship_submissions", ["previous_submission_id"])
    op.create_index(
        "uq_internship_submissions_one_active_draft",
        "internship_submissions",
        ["student_assignment_id"],
        unique=True,
        postgresql_where=sa.text("state = 'DRAFT'"),
    )

    op.create_foreign_key(
        "fk_internship_student_assignments_current_submission",
        "internship_student_assignments",
        "internship_submissions",
        ["current_submission_id"],
        ["id"],
    )

    op.create_table(
        "internship_reviews",
        *_common(),
        sa.Column("student_assignment_id", sa.Uuid(), nullable=False),
        sa.Column("submission_id", sa.Uuid(), nullable=False),
        sa.Column("reviewer_id", sa.Uuid()),
        sa.Column("status", sa.String(30), nullable=False, server_default="ASSIGNED"),
        sa.Column("scores", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("weighted_total", sa.Integer()),
        sa.Column("student_feedback", sa.Text()),
        sa.Column("private_notes", sa.Text()),
        sa.Column("conflict_declared", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("decision", sa.String(30)),
        sa.Column("finalized_at", sa.DateTime(timezone=True)),
        sa.Column("idempotency_key", sa.String(128)),
        sa.ForeignKeyConstraint(["student_assignment_id"], ["internship_student_assignments.id"], name="fk_internship_reviews_assignment"),
        sa.ForeignKeyConstraint(["submission_id"], ["internship_submissions.id"], name="fk_internship_reviews_submission"),
        sa.ForeignKeyConstraint(["reviewer_id"], ["users.id"], name="fk_internship_reviews_reviewer"),
        sa.UniqueConstraint("idempotency_key", name="uq_internship_reviews_idempotency_key"),
        sa.CheckConstraint("weighted_total IS NULL OR weighted_total >= 0", name="ck_internship_reviews_score_nonnegative"),
    )
    op.create_index("ix_internship_reviews_student_assignment_id", "internship_reviews", ["student_assignment_id"])
    op.create_index("ix_internship_reviews_submission_id", "internship_reviews", ["submission_id"])
    op.create_index("ix_internship_reviews_reviewer_id", "internship_reviews", ["reviewer_id"])
    op.create_index("ix_internship_reviews_status", "internship_reviews", ["status"])

    op.create_table(
        "internship_certificates",
        *_common(),
        sa.Column("enrollment_id", sa.Uuid(), nullable=False),
        sa.Column("student_user_id", sa.Uuid(), nullable=False),
        sa.Column("state", sa.String(30), nullable=False, server_default="NOT_ELIGIBLE"),
        sa.Column("public_slug", sa.String(100)),
        sa.Column("public_payload", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("issued_by_id", sa.Uuid()),
        sa.Column("issued_at", sa.DateTime(timezone=True)),
        sa.Column("revoked_by_id", sa.Uuid()),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
        sa.Column("revocation_reason", sa.Text()),
        sa.Column("idempotency_key", sa.String(128)),
        sa.ForeignKeyConstraint(["enrollment_id"], ["internship_cohort_enrollments.id"], name="fk_internship_certificates_enrollment"),
        sa.ForeignKeyConstraint(["student_user_id"], ["users.id"], name="fk_internship_certificates_student"),
        sa.ForeignKeyConstraint(["issued_by_id"], ["users.id"], name="fk_internship_certificates_issuer"),
        sa.ForeignKeyConstraint(["revoked_by_id"], ["users.id"], name="fk_internship_certificates_revoker"),
        sa.UniqueConstraint("enrollment_id", name="uq_internship_certificates_enrollment"),
        sa.UniqueConstraint("public_slug", name="uq_internship_certificates_public_slug"),
        sa.UniqueConstraint("idempotency_key", name="uq_internship_certificates_idempotency_key"),
    )
    op.create_index("ix_internship_certificates_enrollment_id", "internship_certificates", ["enrollment_id"])
    op.create_index("ix_internship_certificates_student_user_id", "internship_certificates", ["student_user_id"])
    op.create_index("ix_internship_certificates_state", "internship_certificates", ["state"])
    op.create_index("ix_internship_certificates_public_slug", "internship_certificates", ["public_slug"])


def downgrade() -> None:
    op.drop_constraint("fk_internship_student_assignments_current_submission", "internship_student_assignments", type_="foreignkey")
    op.drop_index("uq_internship_submissions_one_active_draft", table_name="internship_submissions")
    tables = (
        "internship_certificates",
        "internship_reviews",
        "internship_submissions",
        "internship_uploads",
        "internship_student_assignments",
        "internship_cohort_assignments",
        "internship_assignment_templates",
        "internship_unit_completions",
        "internship_units",
        "internship_weeks",
        "internship_phases",
        "internship_cohort_enrollments",
        "internship_applications",
        "allowed_student_emails",
        "university_email_domains",
        "internship_cohort_tracks",
        "internship_cohorts",
        "internship_track_versions",
        "internship_tracks",
        "internship_programs",
    )
    for table in tables:
        op.drop_table(table)
