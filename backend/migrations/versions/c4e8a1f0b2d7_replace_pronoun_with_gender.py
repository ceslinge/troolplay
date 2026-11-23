"""replace pronoun with grammatical gender

Revision ID: c4e8a1f0b2d7
Revises: 3b1975de5729
Create Date: 2026-11-23 15:00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c4e8a1f0b2d7"
down_revision: str | Sequence[str] | None = "3b1975de5729"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "characters",
        sa.Column(
            "gender", sa.String(length=10), server_default="neutral", nullable=False
        ),
    )
    op.execute(
        "UPDATE characters SET gender = CASE pronoun"
        " WHEN 'elle' THEN 'feminine' WHEN 'il' THEN 'masculine' ELSE 'neutral' END"
    )
    op.drop_constraint(op.f("ck_characters_pronoun"), "characters", type_="check")
    op.drop_column("characters", "pronoun")
    op.create_check_constraint(
        op.f("ck_characters_gender"),
        "characters",
        "gender IN ('feminine', 'masculine', 'neutral')",
    )


def downgrade() -> None:
    op.add_column("characters", sa.Column("pronoun", sa.String(length=4)))
    op.execute(
        "UPDATE characters SET pronoun = CASE gender"
        " WHEN 'feminine' THEN 'elle' WHEN 'masculine' THEN 'il' END"
    )
    op.drop_constraint(op.f("ck_characters_gender"), "characters", type_="check")
    op.drop_column("characters", "gender")
    op.create_check_constraint(
        op.f("ck_characters_pronoun"), "characters", "pronoun IN ('elle', 'il')"
    )
