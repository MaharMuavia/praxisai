"""Enforce NOT NULL on outbox_events.correlation_id to match the ORM model.

The column was introduced nullable in c2d3e4f5a6b7 to avoid breaking existing
rows, but OutboxEvent.correlation_id is a non-optional Mapped[uuid.UUID] with a
uuid4 default, so metadata and schema disagreed and `alembic check` failed.

Revision ID: d5e6f7a8b9c0
Revises: c3d4e5f6a7b8
Create Date: 2026-08-16
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d5e6f7a8b9c0"
down_revision: str | None = "c3d4e5f6a7b8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Backfill any legacy rows persisted while the column permitted NULL before
    # enforcing the constraint. gen_random_uuid() is core in PostgreSQL 13+.
    op.execute(
        "UPDATE outbox_events SET correlation_id = gen_random_uuid() "
        "WHERE correlation_id IS NULL"
    )
    op.alter_column(
        "outbox_events",
        "correlation_id",
        existing_type=sa.Uuid(),
        nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "outbox_events",
        "correlation_id",
        existing_type=sa.Uuid(),
        nullable=True,
    )
