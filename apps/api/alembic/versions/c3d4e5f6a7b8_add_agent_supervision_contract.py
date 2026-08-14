"""Persist the shared supervised agent runtime contract.

Revision ID: c3d4e5f6a7b8
Revises: c2d3e4f5a6b7
Create Date: 2026-08-08
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c3d4e5f6a7b8"
down_revision: str | None = "c2d3e4f5a6b7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "agent_runs",
        sa.Column("runtime_version", sa.String(length=40), nullable=False, server_default="runtime-v1"),
    )
    op.add_column(
        "agent_runs",
        sa.Column("provider", sa.String(length=40), nullable=False, server_default="unknown"),
    )
    op.add_column("agent_runs", sa.Column("resource_version", sa.Integer(), nullable=True))
    op.add_column(
        "agent_runs",
        sa.Column("stale_result", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "agent_runs",
        sa.Column(
            "human_approval_required", sa.Boolean(), nullable=False, server_default=sa.true()
        ),
    )
    op.add_column(
        "agent_runs",
        sa.Column(
            "proposed_actions", sa.JSON(), nullable=False, server_default=sa.text("'[]'"),
        ),
    )
    op.add_column(
        "agent_runs",
        sa.Column(
            "executed_action_evidence", sa.JSON(), nullable=False, server_default=sa.text("'[]'"),
        ),
    )


def downgrade() -> None:
    op.drop_column("agent_runs", "executed_action_evidence")
    op.drop_column("agent_runs", "proposed_actions")
    op.drop_column("agent_runs", "human_approval_required")
    op.drop_column("agent_runs", "stale_result")
    op.drop_column("agent_runs", "resource_version")
    op.drop_column("agent_runs", "provider")
    op.drop_column("agent_runs", "runtime_version")
