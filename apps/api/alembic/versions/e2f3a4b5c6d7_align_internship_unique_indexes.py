"""Align internship unique indexes with model metadata.

Revision ID: e2f3a4b5c6d7
Revises: d1e2f3a4b5c6
Create Date: 2026-08-06
"""

from collections.abc import Sequence

from alembic import op

revision: str = "e2f3a4b5c6d7"
down_revision: str | None = "d1e2f3a4b5c6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


UNIQUE_INDEXES = (
    (
        "internship_programs",
        "uq_internship_programs_slug",
        "ix_internship_programs_slug",
        ["slug"],
    ),
    (
        "internship_tracks",
        "uq_internship_tracks_slug",
        "ix_internship_tracks_slug",
        ["slug"],
    ),
    (
        "internship_uploads",
        "uq_internship_uploads_upload_id",
        "ix_internship_uploads_upload_id",
        ["upload_id"],
    ),
)


def upgrade() -> None:
    for table_name, constraint_name, index_name, columns in UNIQUE_INDEXES:
        op.drop_constraint(constraint_name, table_name, type_="unique")
        op.drop_index(index_name, table_name=table_name)
        op.create_index(index_name, table_name, columns, unique=True)


def downgrade() -> None:
    for table_name, constraint_name, index_name, columns in reversed(UNIQUE_INDEXES):
        op.drop_index(index_name, table_name=table_name)
        op.create_unique_constraint(constraint_name, table_name, columns)
        op.create_index(index_name, table_name, columns)
