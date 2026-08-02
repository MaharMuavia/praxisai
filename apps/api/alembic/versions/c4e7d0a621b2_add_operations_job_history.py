"""add operations job history and export idempotency

Revision ID: c4e7d0a621b2
Revises: a13f4c62e908
Create Date: 2026-07-30 00:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c4e7d0a621b2"
down_revision: str | None = "a13f4c62e908"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("export_jobs") as batch_op:
        batch_op.add_column(sa.Column("idempotency_key", sa.String(length=128), nullable=True))
        batch_op.create_unique_constraint("uq_export_jobs_idempotency_key", ["idempotency_key"])
    op.execute(
        "UPDATE export_jobs SET idempotency_key = 'legacy-' || CAST(id AS VARCHAR) "
        "WHERE idempotency_key IS NULL"
    )
    with op.batch_alter_table("export_jobs") as batch_op:
        batch_op.alter_column("idempotency_key", nullable=False)

    op.create_table(
        "job_attempts",
        sa.Column("outbox_event_id", sa.Uuid(), nullable=False),
        sa.Column("attempt_number", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_category", sa.String(length=100), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
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
        sa.ForeignKeyConstraint(["outbox_event_id"], ["outbox_events.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("outbox_event_id", "attempt_number"),
    )
    op.create_index(
        op.f("ix_job_attempts_outbox_event_id"),
        "job_attempts",
        ["outbox_event_id"],
        unique=False,
    )
    op.create_index(op.f("ix_job_attempts_status"), "job_attempts", ["status"], unique=False)

    op.create_table(
        "outbox_recoveries",
        sa.Column("outbox_event_id", sa.Uuid(), nullable=False),
        sa.Column("recovered_by_id", sa.Uuid(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("idempotency_key", sa.String(length=128), nullable=False),
        sa.Column("recovered_at", sa.DateTime(timezone=True), nullable=False),
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
        sa.ForeignKeyConstraint(["outbox_event_id"], ["outbox_events.id"]),
        sa.ForeignKeyConstraint(["recovered_by_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("idempotency_key"),
    )
    op.create_index(
        op.f("ix_outbox_recoveries_outbox_event_id"),
        "outbox_recoveries",
        ["outbox_event_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_outbox_recoveries_recovered_by_id"),
        "outbox_recoveries",
        ["recovered_by_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_outbox_recoveries_recovered_by_id"), table_name="outbox_recoveries"
    )
    op.drop_index(
        op.f("ix_outbox_recoveries_outbox_event_id"), table_name="outbox_recoveries"
    )
    op.drop_table("outbox_recoveries")
    op.drop_index(op.f("ix_job_attempts_status"), table_name="job_attempts")
    op.drop_index(op.f("ix_job_attempts_outbox_event_id"), table_name="job_attempts")
    op.drop_table("job_attempts")
    with op.batch_alter_table("export_jobs") as batch_op:
        batch_op.drop_constraint("uq_export_jobs_idempotency_key", type_="unique")
        batch_op.drop_column("idempotency_key")
