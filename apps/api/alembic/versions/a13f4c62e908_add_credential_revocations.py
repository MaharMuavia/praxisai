"""add append-only credential revocations

Revision ID: a13f4c62e908
Revises: 6a9b88a3be4c
Create Date: 2026-07-30 00:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a13f4c62e908"
down_revision: str | None = "6a9b88a3be4c"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "credential_revocations",
        sa.Column("credential_id", sa.Uuid(), nullable=False),
        sa.Column("revoked_by_id", sa.Uuid(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("idempotency_key", sa.String(length=128), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["credential_id"], ["credentials.id"]),
        sa.ForeignKeyConstraint(["revoked_by_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("credential_id"),
        sa.UniqueConstraint("idempotency_key"),
    )
    op.create_index(
        op.f("ix_credential_revocations_credential_id"),
        "credential_revocations",
        ["credential_id"],
        unique=True,
    )
    op.create_index(
        op.f("ix_credential_revocations_revoked_by_id"),
        "credential_revocations",
        ["revoked_by_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_credential_revocations_revoked_by_id"),
        table_name="credential_revocations",
    )
    op.drop_index(
        op.f("ix_credential_revocations_credential_id"),
        table_name="credential_revocations",
    )
    op.drop_table("credential_revocations")
