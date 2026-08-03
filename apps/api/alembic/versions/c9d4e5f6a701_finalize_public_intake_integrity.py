"""finalize public intake integrity and privacy lifecycle

Revision ID: c9d4e5f6a701
Revises: b8e2f4a6c901
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c9d4e5f6a701"
down_revision: str | None = "b8e2f4a6c901"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column(
        "public_intake_submissions",
        "contact_email",
        existing_type=sa.String(length=320),
        nullable=True,
    )
    op.create_table(
        "public_intake_idempotencies",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("idempotency_key", sa.String(length=128), nullable=False),
        sa.Column("payload_hash", sa.String(length=64), nullable=False),
        sa.Column("kind", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("submission_id", sa.Uuid(), nullable=True),
        sa.Column("correlation_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["submission_id"], ["public_intake_submissions.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("submission_id"),
    )
    op.create_index(
        "ix_public_intake_idempotencies_idempotency_key",
        "public_intake_idempotencies",
        ["idempotency_key"],
        unique=True,
    )
    op.create_index(
        "ix_public_intake_idempotencies_status",
        "public_intake_idempotencies",
        ["status"],
    )
    op.create_index(
        "ix_public_intake_idempotencies_correlation_id",
        "public_intake_idempotencies",
        ["correlation_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_public_intake_idempotencies_correlation_id", table_name="public_intake_idempotencies")
    op.drop_index("ix_public_intake_idempotencies_status", table_name="public_intake_idempotencies")
    op.drop_index(
        "ix_public_intake_idempotencies_idempotency_key",
        table_name="public_intake_idempotencies",
    )
    op.drop_table("public_intake_idempotencies")
    op.alter_column(
        "public_intake_submissions",
        "contact_email",
        existing_type=sa.String(length=320),
        nullable=False,
    )
