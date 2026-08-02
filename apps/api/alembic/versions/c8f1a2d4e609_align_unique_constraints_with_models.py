"""align unique constraints with model-owned unique indexes

Revision ID: c8f1a2d4e609
Revises: b7d9e4a1c302
Create Date: 2026-08-01
"""

from collections.abc import Sequence

from alembic import op

revision: str = "c8f1a2d4e609"
down_revision: str | None = "b7d9e4a1c302"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Each column retains its model-owned unique index. These table constraints duplicated the
    # same uniqueness guarantee and caused Alembic metadata drift.
    op.drop_constraint(
        "credential_revocations_credential_id_key",
        "credential_revocations",
        type_="unique",
    )
    op.drop_constraint("learning_paths_slug_key", "learning_paths", type_="unique")
    op.drop_constraint(
        "project_opportunities_project_id_key",
        "project_opportunities",
        type_="unique",
    )


def downgrade() -> None:
    op.create_unique_constraint(
        "project_opportunities_project_id_key",
        "project_opportunities",
        ["project_id"],
    )
    op.create_unique_constraint("learning_paths_slug_key", "learning_paths", ["slug"])
    op.create_unique_constraint(
        "credential_revocations_credential_id_key",
        "credential_revocations",
        ["credential_id"],
    )
