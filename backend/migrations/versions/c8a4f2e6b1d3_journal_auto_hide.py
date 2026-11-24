"""journal auto hide

Revision ID: c8a4f2e6b1d3
Revises: b5e1c7d2a9f4
Create Date: 2026-11-24 20:00:00

"""

from collections.abc import Sequence

from alembic import op

revision: str = "c8a4f2e6b1d3"
down_revision: str | Sequence[str] | None = "b5e1c7d2a9f4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

BEFORE = (
    "'decide', 'hide', 'unhide', 'suspend', 'reinstate', "
    "'revoke_reporting', 'restore_reporting', 'set_role'"
)
AFTER = BEFORE + ", 'auto_hide'"


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


def downgrade() -> None:
    # Les masquages automatiques déjà inscrits ne tiennent plus dans l'ancienne liste.
    op.execute("DELETE FROM moderation_actions WHERE action = 'auto_hide'")
    replace(BEFORE)
