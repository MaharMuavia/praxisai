"""add public intake submissions

Revision ID: a7f1c2d3e4b5
Revises: c8f1a2d4e609
Create Date: 2026-08-03 12:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a7f1c2d3e4b5"
down_revision: str | None = "c8f1a2d4e609"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "public_intake_submissions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("kind", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("contact_email", sa.String(length=320), nullable=False),
        sa.Column("source", sa.String(length=120), nullable=True),
        sa.Column("campaign", sa.String(length=120), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("consent_snapshot", sa.JSON(), nullable=False),
        sa.Column("idempotency_key", sa.String(length=128), nullable=False),
        sa.Column("correlation_id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=True),
        sa.Column("qualification_notes", sa.Text(), nullable=True),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_public_intake_submissions_kind", "public_intake_submissions", ["kind"])
    op.create_index("ix_public_intake_submissions_status", "public_intake_submissions", ["status"])
    op.create_index(
        "ix_public_intake_submissions_contact_email", "public_intake_submissions", ["contact_email"]
    )
    op.create_index(
        "ix_public_intake_submissions_idempotency_key",
        "public_intake_submissions",
        ["idempotency_key"],
        unique=True,
    )
    op.create_index(
        "ix_public_intake_submissions_correlation_id",
        "public_intake_submissions",
        ["correlation_id"],
    )
    op.create_index(
        "ix_public_intake_submissions_owner_id", "public_intake_submissions", ["owner_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_public_intake_submissions_owner_id", table_name="public_intake_submissions")
    op.drop_index(
        "ix_public_intake_submissions_correlation_id", table_name="public_intake_submissions"
    )
    op.drop_index(
        "ix_public_intake_submissions_idempotency_key", table_name="public_intake_submissions"
    )
    op.drop_index(
        "ix_public_intake_submissions_contact_email", table_name="public_intake_submissions"
    )
    op.drop_index("ix_public_intake_submissions_status", table_name="public_intake_submissions")
    op.drop_index("ix_public_intake_submissions_kind", table_name="public_intake_submissions")
    op.drop_table("public_intake_submissions")
