"""Deux fiches, un même nom (#122).

Le nom RP peut se partager, comme en jeu : on le dit, sans plus. Le nom en jeu est unique
par serveur dans le jeu : deux fiches qui le portent, c'est un même joueur sur deux comptes,
ou une usurpation. On ne bloque pas (le premier arrivé gagnerait, usurpateur compris), mais
l'équipe reçoit un dossier, et tranche en jeu (charte de modération).

On compare sans majuscules ni accents. Rien ne dit à qui appartient l'autre fiche.
"""

from sqlalchemy import ColumnElement, func, select
from sqlalchemy.orm import Session

from backend.characters.models import Character
from backend.characters.schemas import CharacterOut
from backend.moderation.models import Report


def same(column, value: str) -> ColumnElement[bool]:
    return func.lower(func.unaccent(column)) == func.lower(func.unaccent(value.strip()))


def namesake(
    session: Session,
    server_id: int,
    column,
    value: str | None,
    but: int | None = None,
) -> Character | None:
    """Une autre fiche du serveur qui porte ce nom, ou None."""
    if not value or not value.strip():
        return None
    return session.scalars(
        select(Character)
        .where(
            Character.server_id == server_id,
            Character.is_npc.is_(False),
            Character.id != (but or 0),
            same(column, value),
        )
        .order_by(Character.id)
        .limit(1)
    ).first()


def flag_ingame_twin(session: Session, character: Character) -> None:
    """Un nom en jeu déjà porté sur ce serveur : un dossier pour l'équipe, une seule fois."""
    if character.is_npc or character.server_id is None:
        return
    twin = namesake(
        session,
        character.server_id,
        Character.ingame_name,
        character.ingame_name,
        but=character.id,
    )
    if twin is None:
        return
    already = session.scalar(
        select(Report.id).where(
            Report.automatic.is_(True),
            Report.handled_at.is_(None),
            Report.target_character_id == character.id,
        )
    )
    if already is not None:
        return
    session.add(
        Report(
            automatic=True,
            reporter_id=None,
            reported_user_id=character.user_id,
            reason="impersonation",
            details=(
                f"Même nom en jeu (« {character.ingame_name} ») que la fiche n°{twin.id} "
                f"(« {twin.name} ») sur ce serveur. À vérifier en jeu (charte de modération)."
            ),
            snapshot=CharacterOut.model_validate(character).model_dump(mode="json"),
            target_character_id=character.id,
        )
    )
