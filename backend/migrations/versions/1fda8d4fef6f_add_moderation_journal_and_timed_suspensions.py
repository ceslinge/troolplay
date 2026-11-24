"""add moderation journal and timed suspensions

Revision ID: 1fda8d4fef6f
Revises: 0de9f6cce6a3
Create Date: 2026-11-24 16:06:49

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "1fda8d4fef6f"
down_revision: str | Sequence[str] | None = "0de9f6cce6a3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "moderation_actions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("actor_id", sa.Integer(), nullable=True),
        sa.Column("action", sa.String(length=20), nullable=False),
        sa.Column("target_user_id", sa.Integer(), nullable=True),
        sa.Column("target_character_id", sa.Integer(), nullable=True),
        sa.Column("target_story_id", sa.Integer(), nullable=True),
        sa.Column("detail", sa.String(length=20), nullable=True),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "action IN ('decide', 'hide', 'unhide', 'suspend', 'reinstate', 'revoke_reporting', 'restore_reporting')",
            name=op.f("ck_moderation_actions_action"),
        ),
        sa.ForeignKeyConstraint(
            ["actor_id"],
            ["users.id"],
            name=op.f("fk_moderation_actions_actor_id_users"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["target_character_id"],
            ["characters.id"],
            name=op.f("fk_moderation_actions_target_character_id_characters"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["target_story_id"],
            ["stories.id"],
            name=op.f("fk_moderation_actions_target_story_id_stories"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["target_user_id"],
            ["users.id"],
            name=op.f("fk_moderation_actions_target_user_id_users"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_moderation_actions")),
    )
    op.create_index(
        op.f("ix_moderation_actions_action"),
        "moderation_actions",
        ["action"],
        unique=False,
    )
    op.create_index(
        op.f("ix_moderation_actions_actor_id"),
        "moderation_actions",
        ["actor_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_moderation_actions_created_at"),
        "moderation_actions",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_moderation_actions_target_user_id"),
        "moderation_actions",
        ["target_user_id"],
        unique=False,
    )
    op.add_column(
        "users", sa.Column("banned_until", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "users",
        sa.Column("report_banned_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Alembic ne voit pas les contraintes de vérification : celle-ci est ajoutée à la main.
    op.create_check_constraint(
        op.f("ck_reports_decision"),
        "reports",
        "decision IS NULL OR decision IN ('founded', 'no_action', 'abusive')",
    )


def downgrade() -> None:
    op.drop_constraint(op.f("ck_reports_decision"), "reports", type_="check")
    op.drop_column("users", "report_banned_at")
    op.drop_column("users", "banned_until")
    op.drop_index(
        op.f("ix_moderation_actions_target_user_id"), table_name="moderation_actions"
    )
    op.drop_index(
        op.f("ix_moderation_actions_created_at"), table_name="moderation_actions"
    )
    op.drop_index(
        op.f("ix_moderation_actions_actor_id"), table_name="moderation_actions"
    )
    op.drop_index(op.f("ix_moderation_actions_action"), table_name="moderation_actions")
    op.drop_table("moderation_actions")
