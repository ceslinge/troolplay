"""contests

Une contestation par décision (#141), et sa réponse au journal.

Revision ID: 04b4435ef623
Revises: e4b9d1c7a2f6
Create Date: 2026-11-25 14:00:12.740478

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "04b4435ef623"
down_revision: str | Sequence[str] | None = "e4b9d1c7a2f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

BEFORE = (
    "'decide', 'hide', 'unhide', 'suspend', 'reinstate', "
    "'revoke_reporting', 'restore_reporting', 'set_role', 'auto_hide', "
    "'add_server', 'rename_server', 'close_server', 'reopen_server'"
)
AFTER = BEFORE + ", 'answer_contest'"


def replace(actions: str) -> None:
    # Alembic ne voit pas les contraintes de vérification : on les remplace à la main.
    op.drop_constraint(
        op.f("ck_moderation_actions_action"), "moderation_actions", type_="check"
    )
    op.create_check_constraint(
        op.f("ck_moderation_actions_action"),
        "moderation_actions",
        f"action IN ({actions})",
    )


def upgrade() -> None:
    replace(AFTER)
    op.create_table(
        "contests",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("action_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("answer", sa.Text(), nullable=True),
        sa.Column("outcome", sa.String(length=10), nullable=True),
        sa.Column("answered_by", sa.Integer(), nullable=True),
        sa.Column("answered_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "outcome IS NULL OR outcome IN ('upheld', 'lifted')",
            name=op.f("ck_contests_outcome"),
        ),
        sa.ForeignKeyConstraint(
            ["action_id"],
            ["moderation_actions.id"],
            name=op.f("fk_contests_action_id_moderation_actions"),
        ),
        sa.ForeignKeyConstraint(
            ["answered_by"],
            ["users.id"],
            name=op.f("fk_contests_answered_by_users"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_contests_user_id_users"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_contests")),
        sa.UniqueConstraint("action_id", name=op.f("uq_contests_action_id")),
    )
    op.create_index(op.f("ix_contests_user_id"), "contests", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_contests_user_id"), table_name="contests")
    op.drop_table("contests")
    op.execute("DELETE FROM moderation_actions WHERE action = 'answer_contest'")
    replace(BEFORE)
