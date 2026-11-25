"""automatic reports

Un dossier ouvert par le site lui-même : un doublon de nom en jeu (#122).

Revision ID: c879186098ef
Revises: bb0c665fc619
Create Date: 2026-11-25 22:56:46.531201

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c879186098ef"
down_revision: str | Sequence[str] | None = "bb0c665fc619"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "reports",
        sa.Column(
            "automatic", sa.Boolean(), server_default=sa.text("false"), nullable=False
        ),
    )


def downgrade() -> None:
    op.drop_column("reports", "automatic")
