"""enable unaccent

Revision ID: a7d4e2c9b1f6
Revises: 9bc36912abf0
Create Date: 2026-11-23 21:00:00

"""

from collections.abc import Sequence

from alembic import op

revision: str = "a7d4e2c9b1f6"
down_revision: str | Sequence[str] | None = "9bc36912abf0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Pour chercher « maelis » et trouver « Maëlis ». Extension fournie avec Postgres,
    # et « de confiance » : le propriétaire de la base peut l'installer sans être superutilisateur.
    op.execute("CREATE EXTENSION IF NOT EXISTS unaccent")


def downgrade() -> None:
    op.execute("DROP EXTENSION IF EXISTS unaccent")
