"""add external payout evidence

Revision ID: f4c2d1a9b807
Revises: e7b3c8f2a109
Create Date: 2026-07-30
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "f4c2d1a9b807"
down_revision: str | None = "e7b3c8f2a109"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("payouts", sa.Column("evidence_hash", sa.String(length=64), nullable=True))
    op.add_column(
        "payouts",
        sa.Column("idempotency_key", sa.String(length=128), nullable=True),
    )
    op.create_index(
        "ix_payouts_idempotency_key",
        "payouts",
        ["idempotency_key"],
        unique=True,
    )
    op.drop_index("ix_payouts_allocation_id", table_name="payouts")
    op.create_index(
        "ix_payouts_allocation_id",
        "payouts",
        ["allocation_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_payouts_allocation_id", table_name="payouts")
    op.create_index(
        "ix_payouts_allocation_id",
        "payouts",
        ["allocation_id"],
        unique=False,
    )
    op.drop_index("ix_payouts_idempotency_key", table_name="payouts")
    op.drop_column("payouts", "idempotency_key")
    op.drop_column("payouts", "evidence_hash")
