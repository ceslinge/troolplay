"""restrict classes to the game list

Revision ID: e1a7c3d9f5b2
Revises: c4e8a1f0b2d7
Create Date: 2026-11-23 17:00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "e1a7c3d9f5b2"
down_revision: str | Sequence[str] | None = "c4e8a1f0b2d7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Liste figée à la date de la migration : si le jeu ajoute une classe,
# une nouvelle migration mettra la contrainte à jour.
CLASSES = (
    "feca", "osamodas", "enutrof", "sram", "xelor", "ecaflip", "eniripsa", "iop",
    "cra", "sadida", "sacrieur", "pandawa", "roublard", "zobal", "steamer",
    "eliotrope", "huppermage", "ouginak", "forgelance",
)  # fmt: skip


def upgrade() -> None:
    # Les anciennes valeurs libres (« Crâ ») deviennent leur identifiant (« cra »).
    # Une valeur qui ne correspond à aucune classe est vidée : le mystère est permis.
    op.execute(
        "UPDATE characters SET class = lower(translate(class, 'âéèêëÉÈ', 'aeeeeee'))"
    )
    values = ", ".join(f"'{c}'" for c in CLASSES)
    op.execute(f"UPDATE characters SET class = NULL WHERE class NOT IN ({values})")
    op.alter_column(
        "characters", "class", type_=sa.String(length=20), existing_nullable=True
    )
    op.create_check_constraint(
        op.f("ck_characters_class"), "characters", f"class IN ({values})"
    )


def downgrade() -> None:
    op.drop_constraint(op.f("ck_characters_class"), "characters", type_="check")
    op.alter_column(
        "characters", "class", type_=sa.String(length=30), existing_nullable=True
    )
