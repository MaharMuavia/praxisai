"""harden transition replay scope and add outbox correlation metadata

Revision ID: c2d3e4f5a6b7
Revises: f6b2c3d4e5f6
Create Date: 2026-08-08
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c2d3e4f5a6b7"
down_revision: str | None = "f6b2c3d4e5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("project_transitions") as batch_op:
        batch_op.add_column(sa.Column("organization_id", sa.Uuid(), nullable=True))
        batch_op.add_column(
            sa.Column("operation", sa.String(length=80), nullable=False, server_default="project.transition")
        )
        batch_op.add_column(sa.Column("request_hash", sa.String(length=64), nullable=True))
        batch_op.create_foreign_key(
            "fk_project_transitions_organization_id", "organizations", ["organization_id"], ["id"]
        )
        batch_op.create_index("ix_project_transitions_organization_id", ["organization_id"])
        batch_op.create_index("ix_project_transitions_request_hash", ["request_hash"])

    with op.batch_alter_table("outbox_events") as batch_op:
        batch_op.add_column(sa.Column("correlation_id", sa.Uuid(), nullable=True))
        batch_op.create_index("ix_outbox_events_correlation_id", ["correlation_id"])


def downgrade() -> None:
    with op.batch_alter_table("outbox_events") as batch_op:
        batch_op.drop_index("ix_outbox_events_correlation_id")
        batch_op.drop_column("correlation_id")
    with op.batch_alter_table("project_transitions") as batch_op:
        batch_op.drop_index("ix_project_transitions_request_hash")
        batch_op.drop_index("ix_project_transitions_organization_id")
        batch_op.drop_constraint("fk_project_transitions_organization_id", type_="foreignkey")
        batch_op.drop_column("request_hash")
        batch_op.drop_column("operation")
        batch_op.drop_column("organization_id")
