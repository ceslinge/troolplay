from sqlalchemy import ColumnElement, select, true

from backend.accounts.models import User
from backend.characters.models import Character
from backend.ignores.models import IgnoredCharacter


def not_ignored(viewer: User | None, column=Character.id) -> ColumnElement[bool]:
    """Pour une requête : les personnages que cette personne n'ignore pas. Un visiteur voit tout."""
    if viewer is None:
        return true()
    return column.not_in(
        select(IgnoredCharacter.character_id).where(
            IgnoredCharacter.user_id == viewer.id
        )
    )
