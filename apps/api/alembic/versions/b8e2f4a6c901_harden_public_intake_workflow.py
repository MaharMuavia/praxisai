"""harden public intake workflow and privacy fields

Revision ID: b8e2f4a6c901
Revises: a7f1c2d3e4b5
Create Date: 2026-08-03 14:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b8e2f4a6c901"
down_revision: str | None = "a7f1c2d3e4b5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "public_intake_submissions",
        sa.Column("payload_hash", sa.String(length=64), nullable=False, server_default=""),
    )
    op.add_column(
        "public_intake_submissions",
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
    )
    op.add_column(
        "public_intake_submissions", sa.Column("conversion_evidence", sa.Text(), nullable=True)
    )
    op.add_column(
        "public_intake_submissions",
        sa.Column("retention_expires_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "public_intake_submissions", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "public_intake_submissions",
        sa.Column("anonymized_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "public_intake_submissions",
        sa.Column("withdrawal_requested_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_public_intake_submissions_payload_hash",
        "public_intake_submissions",
        ["payload_hash"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_public_intake_submissions_payload_hash", table_name="public_intake_submissions"
    )
    for column in (
        "withdrawal_requested_at",
        "anonymized_at",
        "deleted_at",
        "retention_expires_at",
        "conversion_evidence",
        "version",
        "payload_hash",
    ):
        op.drop_column("public_intake_submissions", column)
