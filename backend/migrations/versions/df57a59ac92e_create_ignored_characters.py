"""create ignored characters

Revision ID: df57a59ac92e
Revises: c8a4f2e6b1d3
Create Date: 2026-11-24 20:17:33

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "df57a59ac92e"
down_revision: str | Sequence[str] | None = "c8a4f2e6b1d3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "ignored_characters",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("character_id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["character_id"],
            ["characters.id"],
            name=op.f("fk_ignored_characters_character_id_characters"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_ignored_characters_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "user_id", "character_id", name=op.f("pk_ignored_characters")
        ),
    )
    op.create_index(
        op.f("ix_ignored_characters_character_id"),
        "ignored_characters",
        ["character_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_ignored_characters_character_id"), table_name="ignored_characters"
    )
    op.drop_table("ignored_characters")
