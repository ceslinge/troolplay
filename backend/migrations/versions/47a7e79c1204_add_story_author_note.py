"""add story author note

Revision ID: 47a7e79c1204
Revises: aaca0e4a0f34
Create Date: 2026-11-24 15:17:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "47a7e79c1204"
down_revision: str | Sequence[str] | None = "aaca0e4a0f34"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "stories", sa.Column("author_note", sa.String(length=1000), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("stories", "author_note")
