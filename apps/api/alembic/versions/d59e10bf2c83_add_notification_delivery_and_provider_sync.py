"""add notification delivery controls and provider synchronization

Revision ID: d59e10bf2c83
Revises: c4e7d0a621b2
Create Date: 2026-07-30 00:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d59e10bf2c83"
down_revision: str | None = "c4e7d0a621b2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("notifications") as batch_op:
        batch_op.add_column(sa.Column("source_outbox_event_id", sa.Uuid(), nullable=True))
        batch_op.create_foreign_key(
            "fk_notifications_source_outbox_event_id",
            "outbox_events",
            ["source_outbox_event_id"],
            ["id"],
        )
        batch_op.create_unique_constraint(
            "uq_notifications_user_source_event", ["user_id", "source_outbox_event_id"]
        )
        batch_op.create_index(
            "ix_notifications_source_outbox_event_id", ["source_outbox_event_id"]
        )

    op.create_table(
        "notification_preferences",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("category", sa.String(length=40), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
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
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "category"),
    )
    op.create_index(
        op.f("ix_notification_preferences_user_id"),
        "notification_preferences",
        ["user_id"],
        unique=False,
    )

    op.create_table(
        "provider_synchronizations",
        sa.Column("provider", sa.String(length=60), nullable=False),
        sa.Column("operation", sa.String(length=80), nullable=False),
        sa.Column("mode", sa.String(length=30), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("resource_type", sa.String(length=60), nullable=False),
        sa.Column("resource_id", sa.Uuid(), nullable=True),
        sa.Column("correlation_id", sa.Uuid(), nullable=False),
        sa.Column("error_category", sa.String(length=100), nullable=True),
        sa.Column("details", sa.JSON(), nullable=False),
        sa.Column("checked_at", sa.DateTime(timezone=True), nullable=False),
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
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_provider_synchronizations_provider"),
        "provider_synchronizations",
        ["provider"],
        unique=False,
    )
    op.create_index(
        op.f("ix_provider_synchronizations_status"),
        "provider_synchronizations",
        ["status"],
        unique=False,
    )
    op.create_index(
        op.f("ix_provider_synchronizations_resource_id"),
        "provider_synchronizations",
        ["resource_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_provider_synchronizations_correlation_id"),
        "provider_synchronizations",
        ["correlation_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_provider_synchronizations_correlation_id"),
        table_name="provider_synchronizations",
    )
    op.drop_index(
        op.f("ix_provider_synchronizations_resource_id"),
        table_name="provider_synchronizations",
    )
    op.drop_index(
        op.f("ix_provider_synchronizations_status"),
        table_name="provider_synchronizations",
    )
    op.drop_index(
        op.f("ix_provider_synchronizations_provider"),
        table_name="provider_synchronizations",
    )
    op.drop_table("provider_synchronizations")
    op.drop_index(
        op.f("ix_notification_preferences_user_id"), table_name="notification_preferences"
    )
    op.drop_table("notification_preferences")
    with op.batch_alter_table("notifications") as batch_op:
        batch_op.drop_index("ix_notifications_source_outbox_event_id")
        batch_op.drop_constraint("uq_notifications_user_source_event", type_="unique")
        batch_op.drop_constraint("fk_notifications_source_outbox_event_id", type_="foreignkey")
        batch_op.drop_column("source_outbox_event_id")
