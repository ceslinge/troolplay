"""journal role changes

Revision ID: b5e1c7d2a9f4
Revises: 1fda8d4fef6f
Create Date: 2026-11-24 18:00:00

"""

from collections.abc import Sequence

from alembic import op

revision: str = "b5e1c7d2a9f4"
down_revision: str | Sequence[str] | None = "1fda8d4fef6f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

BEFORE = (
    "'decide', 'hide', 'unhide', 'suspend', 'reinstate', "
    "'revoke_reporting', 'restore_reporting'"
)
AFTER = BEFORE + ", 'set_role'"


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
    # Les changements de rôle déjà inscrits ne tiennent plus dans l'ancienne liste.
    op.execute("DELETE FROM moderation_actions WHERE action = 'set_role'")
    replace(BEFORE)
