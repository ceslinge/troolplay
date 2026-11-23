"""add character position

Revision ID: c9f6a4b2d3e5
Revises: a7d4e2c9b1f6
Create Date: 2026-11-24 00:30:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c9f6a4b2d3e5"
down_revision: str | Sequence[str] | None = "a7d4e2c9b1f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "characters",
        sa.Column("position", sa.SmallInteger(), server_default="0", nullable=False),
    )
    # Les personnages existants gardent l'ordre qu'ils avaient : par nom.
    op.execute(
        """
        UPDATE characters AS c
        SET position = ranked.position
        FROM (
            SELECT id, row_number() OVER (
                PARTITION BY user_id ORDER BY name, id
            ) AS position
            FROM characters
            WHERE user_id IS NOT NULL
        ) AS ranked
        WHERE c.id = ranked.id
        """
    )


def downgrade() -> None:
    op.drop_column("characters", "position")
