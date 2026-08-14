"""Add optimistic concurrency and idempotency to completion decisions.

Revision ID: f5a1b2c3d4e5
Revises: d1e2f3a4b5c6
Create Date: 2026-08-06
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "f5a1b2c3d4e5"
down_revision: str | None = "d1e2f3a4b5c6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "internship_cohort_enrollments",
        sa.Column("completion_decision_idempotency_key", sa.String(128), nullable=True),
    )
    op.add_column(
        "internship_cohort_enrollments",
        sa.Column("completion_decision_reason", sa.Text(), nullable=True),
    )
    op.create_unique_constraint(
        "uq_internship_enrollments_completion_decision_key",
        "internship_cohort_enrollments",
        ["completion_decision_idempotency_key"],
    )
    op.add_column("internship_uploads", sa.Column("scan_provider", sa.String(40), nullable=True))
    op.add_column("internship_uploads", sa.Column("scanned_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column(
        "internship_uploads",
        sa.Column("scan_evidence", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_internship_enrollments_completion_decision_key",
        "internship_cohort_enrollments",
        type_="unique",
    )
    op.drop_column("internship_cohort_enrollments", "completion_decision_reason")
    op.drop_column("internship_cohort_enrollments", "completion_decision_idempotency_key")
    op.drop_column("internship_uploads", "scan_evidence")
    op.drop_column("internship_uploads", "scanned_at")
    op.drop_column("internship_uploads", "scan_provider")
