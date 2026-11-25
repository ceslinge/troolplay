"""servers from site

Revision ID: e4b9d1c7a2f6
Revises: df57a59ac92e
Create Date: 2026-11-25 10:30:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "e4b9d1c7a2f6"
down_revision: str | Sequence[str] | None = "df57a59ac92e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

BEFORE = (
    "'decide', 'hide', 'unhide', 'suspend', 'reinstate', "
    "'revoke_reporting', 'restore_reporting', 'set_role', 'auto_hide'"
)
SERVER_ACTIONS = "'add_server', 'rename_server', 'close_server', 'reopen_server'"
AFTER = f"{BEFORE}, {SERVER_ACTIONS}"


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
    op.add_column(
        "game_servers", sa.Column("catalog_name", sa.String(length=40), nullable=True)
    )
    # Jusqu'ici, tous les serveurs venaient du catalogue.
    op.execute("UPDATE game_servers SET catalog_name = name")
    op.add_column(
        "moderation_actions",
        sa.Column("target_server_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        op.f("fk_moderation_actions_target_server_id_game_servers"),
        "moderation_actions",
        "game_servers",
        ["target_server_id"],
        ["id"],
        ondelete="SET NULL",
    )
    # Un ancien nom de serveur tient jusqu'à 40 caractères.
    op.alter_column(
        "moderation_actions",
        "detail",
        type_=sa.String(length=40),
        existing_type=sa.String(length=20),
    )
    replace(AFTER)


def downgrade() -> None:
    op.execute(f"DELETE FROM moderation_actions WHERE action IN ({SERVER_ACTIONS})")
    replace(BEFORE)
    op.alter_column(
        "moderation_actions",
        "detail",
        type_=sa.String(length=20),
        existing_type=sa.String(length=40),
    )
    op.drop_constraint(
        op.f("fk_moderation_actions_target_server_id_game_servers"),
        "moderation_actions",
        type_="foreignkey",
    )
    op.drop_column("moderation_actions", "target_server_id")
    op.drop_column("game_servers", "catalog_name")
