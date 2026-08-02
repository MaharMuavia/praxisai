"""add learning paths and student proposal marketplace

Revision ID: b7d9e4a1c302
Revises: f4c2d1a9b807
Create Date: 2026-07-31
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b7d9e4a1c302"
down_revision: str | None = "f4c2d1a9b807"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _entity_columns() -> list[sa.Column[object]]:
    return [
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    ]


def upgrade() -> None:
    op.create_table(
        "learning_paths",
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("level", sa.String(length=30), nullable=False),
        sa.Column("estimated_hours", sa.Integer(), nullable=False),
        sa.Column("skill_outcomes", sa.JSON(), nullable=False),
        sa.Column("prerequisites", sa.JSON(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("is_demo", sa.Boolean(), nullable=False),
        *_entity_columns(),
        sa.CheckConstraint("estimated_hours > 0"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index("ix_learning_paths_slug", "learning_paths", ["slug"], unique=True)
    op.create_index("ix_learning_paths_active", "learning_paths", ["active"])
    op.create_table(
        "learning_modules",
        sa.Column("learning_path_id", sa.Uuid(), nullable=False),
        sa.Column("ordinal", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("estimated_minutes", sa.Integer(), nullable=False),
        sa.Column("content_sections", sa.JSON(), nullable=False),
        sa.Column("exercise_brief", sa.Text(), nullable=False),
        sa.Column("completion_evidence", sa.Text(), nullable=False),
        *_entity_columns(),
        sa.ForeignKeyConstraint(["learning_path_id"], ["learning_paths.id"]),
        sa.UniqueConstraint("learning_path_id", "ordinal"),
    )
    op.create_index("ix_learning_modules_learning_path_id", "learning_modules", ["learning_path_id"])
    op.create_table(
        "learning_enrollments",
        sa.Column("learning_path_id", sa.Uuid(), nullable=False),
        sa.Column("student_user_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("enrolled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        *_entity_columns(),
        sa.ForeignKeyConstraint(["learning_path_id"], ["learning_paths.id"]),
        sa.ForeignKeyConstraint(["student_user_id"], ["users.id"]),
        sa.UniqueConstraint("learning_path_id", "student_user_id"),
    )
    op.create_index("ix_learning_enrollments_learning_path_id", "learning_enrollments", ["learning_path_id"])
    op.create_index("ix_learning_enrollments_student_user_id", "learning_enrollments", ["student_user_id"])
    op.create_table(
        "learning_module_completions",
        sa.Column("enrollment_id", sa.Uuid(), nullable=False),
        sa.Column("learning_module_id", sa.Uuid(), nullable=False),
        sa.Column("evidence_summary", sa.Text(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=False),
        *_entity_columns(),
        sa.ForeignKeyConstraint(["enrollment_id"], ["learning_enrollments.id"]),
        sa.ForeignKeyConstraint(["learning_module_id"], ["learning_modules.id"]),
        sa.UniqueConstraint("enrollment_id", "learning_module_id"),
    )
    op.create_index("ix_learning_module_completions_enrollment_id", "learning_module_completions", ["enrollment_id"])
    op.create_index("ix_learning_module_completions_learning_module_id", "learning_module_completions", ["learning_module_id"])
    op.create_table(
        "project_opportunities",
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("published_by_id", sa.Uuid(), nullable=False),
        sa.Column("headline", sa.String(length=200), nullable=False),
        sa.Column("brief", sa.Text(), nullable=False),
        sa.Column("required_skills", sa.JSON(), nullable=False),
        sa.Column("nice_to_have_skills", sa.JSON(), nullable=False),
        sa.Column("deliverables", sa.JSON(), nullable=False),
        sa.Column("proposal_requirements", sa.JSON(), nullable=False),
        sa.Column("estimated_hours_low", sa.Integer(), nullable=False),
        sa.Column("estimated_hours_high", sa.Integer(), nullable=False),
        sa.Column("budget_minor", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("deadline", sa.DateTime(timezone=True), nullable=False),
        sa.Column("supervision_level", sa.String(length=30), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("max_proposals", sa.Integer(), nullable=False),
        *_entity_columns(),
        sa.CheckConstraint("estimated_hours_low > 0"),
        sa.CheckConstraint("estimated_hours_high >= estimated_hours_low"),
        sa.CheckConstraint("budget_minor > 0"),
        sa.CheckConstraint("max_proposals > 0"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.ForeignKeyConstraint(["published_by_id"], ["users.id"]),
        sa.UniqueConstraint("project_id"),
    )
    op.create_index("ix_project_opportunities_project_id", "project_opportunities", ["project_id"], unique=True)
    op.create_index("ix_project_opportunities_published_by_id", "project_opportunities", ["published_by_id"])
    op.create_index("ix_project_opportunities_status", "project_opportunities", ["status"])
    op.create_table(
        "student_proposals",
        sa.Column("opportunity_id", sa.Uuid(), nullable=False),
        sa.Column("student_user_id", sa.Uuid(), nullable=False),
        sa.Column("cover_note", sa.Text(), nullable=False),
        sa.Column("approach", sa.Text(), nullable=False),
        sa.Column("delivery_plan", sa.JSON(), nullable=False),
        sa.Column("relevant_evidence", sa.JSON(), nullable=False),
        sa.Column("proposed_amount_minor", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("estimated_days", sa.Integer(), nullable=False),
        sa.Column("availability_hours_per_week", sa.Integer(), nullable=False),
        sa.Column("state", sa.String(length=30), nullable=False),
        sa.Column("submission_idempotency_key", sa.String(length=128), nullable=False),
        sa.Column("submission_hash", sa.String(length=64), nullable=False),
        sa.Column("decided_by_id", sa.Uuid(), nullable=True),
        sa.Column("decision_reason", sa.Text(), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("decision_idempotency_key", sa.String(length=128), nullable=True),
        *_entity_columns(),
        sa.CheckConstraint("proposed_amount_minor > 0"),
        sa.CheckConstraint("estimated_days > 0"),
        sa.CheckConstraint("availability_hours_per_week > 0"),
        sa.ForeignKeyConstraint(["decided_by_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["opportunity_id"], ["project_opportunities.id"]),
        sa.ForeignKeyConstraint(["student_user_id"], ["users.id"]),
        sa.UniqueConstraint("opportunity_id", "student_user_id"),
    )
    op.create_index("ix_student_proposals_opportunity_id", "student_proposals", ["opportunity_id"])
    op.create_index("ix_student_proposals_student_user_id", "student_proposals", ["student_user_id"])
    op.create_index("ix_student_proposals_state", "student_proposals", ["state"])
    op.create_index(
        "ix_student_proposals_submission_idempotency_key",
        "student_proposals",
        ["submission_idempotency_key"],
        unique=True,
    )
    op.create_index(
        "ix_student_proposals_decision_idempotency_key",
        "student_proposals",
        ["decision_idempotency_key"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_table("student_proposals")
    op.drop_table("project_opportunities")
    op.drop_table("learning_module_completions")
    op.drop_table("learning_enrollments")
    op.drop_table("learning_modules")
    op.drop_table("learning_paths")
