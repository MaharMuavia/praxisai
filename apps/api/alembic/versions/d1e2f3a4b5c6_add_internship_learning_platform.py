"""add internship learning and project execution domain

Revision ID: d1e2f3a4b5c6
Revises: c8f1a2d4e609
Create Date: 2026-08-04
"""

from collections.abc import Sequence

from alembic import op

from app.domain.models import Base

revision: str = "d1e2f3a4b5c6"
down_revision: str | None = "c9d4e5f6a701"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


INTERNSHIP_TABLES = (
    "internship_programs",
    "internship_tracks",
    "internship_track_versions",
    "internship_cohorts",
    "internship_cohort_tracks",
    "allowed_student_emails",
    "internship_applications",
    "internship_cohort_enrollments",
    "internship_phases",
    "internship_weeks",
    "internship_units",
    "internship_unit_completions",
    "internship_assignment_templates",
    "internship_cohort_assignments",
    "internship_student_assignments",
    "internship_uploads",
    "internship_submissions",
    "internship_reviews",
    "internship_certificates",
    "university_email_domains",
)


def upgrade() -> None:
    # The model metadata is the source of truth for these normalized tables. The
    # explicit table allow-list prevents this migration from touching existing
    # commercial, learning, or credential tables.
    bind = op.get_bind()
    tables = [Base.metadata.tables[name] for name in INTERNSHIP_TABLES]
    Base.metadata.create_all(bind=bind, tables=tables, checkfirst=False)


def downgrade() -> None:
    bind = op.get_bind()
    tables = [Base.metadata.tables[name] for name in reversed(INTERNSHIP_TABLES)]
    Base.metadata.drop_all(bind=bind, tables=tables, checkfirst=False)
