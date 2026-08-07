"""Merge the internship and platform migration branches.

Revision ID: f6b2c3d4e5f6
Revises: e2f3a4b5c6d7, f5a1b2c3d4e5
Create Date: 2026-08-06
"""

from collections.abc import Sequence

revision: str = "f6b2c3d4e5f6"
down_revision: tuple[str, str] = ("e2f3a4b5c6d7", "f5a1b2c3d4e5")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
