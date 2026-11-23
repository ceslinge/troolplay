"""add bellaphone class

Revision ID: f3b9d2e6a8c4
Revises: e1a7c3d9f5b2
Create Date: 2026-11-23 17:30:00

"""

from collections.abc import Sequence

from alembic import op

revision: str = "f3b9d2e6a8c4"
down_revision: str | Sequence[str] | None = "e1a7c3d9f5b2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

BEFORE = (
    "feca", "osamodas", "enutrof", "sram", "xelor", "ecaflip", "eniripsa", "iop",
    "cra", "sadida", "sacrieur", "pandawa", "roublard", "zobal", "steamer",
    "eliotrope", "huppermage", "ouginak", "forgelance",
)  # fmt: skip
AFTER = (*BEFORE, "bellaphone")


def replace_constraint(classes: tuple[str, ...]) -> None:
    values = ", ".join(f"'{c}'" for c in classes)
    op.drop_constraint(op.f("ck_characters_class"), "characters", type_="check")
    op.create_check_constraint(
        op.f("ck_characters_class"), "characters", f"class IN ({values})"
    )


def upgrade() -> None:
    replace_constraint(AFTER)


def downgrade() -> None:
    op.execute("UPDATE characters SET class = NULL WHERE class = 'bellaphone'")
    replace_constraint(BEFORE)
