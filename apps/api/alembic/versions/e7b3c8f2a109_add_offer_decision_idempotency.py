"""add offer decision idempotency

Revision ID: e7b3c8f2a109
Revises: d59e10bf2c83
Create Date: 2026-07-30
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "e7b3c8f2a109"
down_revision: str | None = "d59e10bf2c83"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "assignment_offers",
        sa.Column("decision_idempotency_key", sa.String(length=128), nullable=True),
    )
    op.create_index(
        "ix_assignment_offers_decision_idempotency_key",
        "assignment_offers",
        ["decision_idempotency_key"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_assignment_offers_decision_idempotency_key",
        table_name="assignment_offers",
    )
    op.drop_column("assignment_offers", "decision_idempotency_key")
