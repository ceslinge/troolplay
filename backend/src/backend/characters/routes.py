from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Response
from sqlalchemy import delete, func, or_, select
from sqlalchemy.orm import Session, selectinload

from backend.accounts.models import User
from backend.accounts.roles import Capability, can
from backend.accounts.sessions import CurrentUser, OptionalUser
from backend.characters.classes import is_available
from backend.characters.models import Character, CharacterHangout
from backend.characters.schemas import (
    CharacterCreate,
    CharacterList,
    CharacterOrder,
    CharacterOut,
    CharacterOwnedOut,
    CharacterOwnedSummary,
    CharacterSummary,
    CharacterUpdate,
    HangoutIn,
    HangoutOut,
    MyCharacters,
    Period,
)
from backend.db import SessionDep
from backend.errors import field_error
from backend.ignores.filters import not_ignored
from backend.ignores.models import IgnoredCharacter
from backend.servers.models import GameServer

router = APIRouter(prefix="/characters", tags=["characters"])

# Assez pour plusieurs vies, pas au point d'encombrer la barre (ni l'annuaire).
MAX_CHARACTERS = 10


@router.get("")
def list_characters(
    session: SessionDep,
    viewer: OptionalUser,
    server_id: int,
    day: Annotated[int | None, Query(ge=1, le=7)] = None,
    period: Period | None = None,
    q: Annotated[str | None, Query(max_length=60)] = None,
    include_inactive: bool = False,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> CharacterList:
    if session.get(GameServer, server_id) is None:
        raise HTTPException(status_code=404, detail="Serveur introuvable")

    query = select(Character).where(
        Character.server_id == server_id,
        Character.hidden_at.is_(None),
        not_ignored(viewer),
    )
    if day is not None:
        query = query.where(Character.play_days.contains([day]))
    if period is not None:
        query = query.where(Character.play_periods.contains([period]))
    if q and q.strip():
        query = query.where(matches_name(q.strip()))
    if not include_inactive:
        query = query.where(Character.inactive_at.is_(None))

    total = session.scalar(select(func.count()).select_from(query.subquery())) or 0
    characters = session.scalars(
        query.options(selectinload(Character.server))
        .order_by(Character.name, Character.id)
        .limit(limit)
        .offset(offset)
    )
    return CharacterList(
        items=[CharacterSummary.model_validate(c) for c in characters], total=total
    )


def matches_name(text: str):
    """Le nom ou le nom en jeu contient ce texte, sans tenir compte des accents ni des majuscules."""
    # % et _ tapés par quelqu'un sont des caractères comme les autres, pas des jokers.
    escaped = text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    pattern = func.unaccent(f"%{escaped}%")
    return or_(
        func.unaccent(Character.name).ilike(pattern, escape="\\"),
        func.unaccent(Character.ingame_name).ilike(pattern, escape="\\"),
    )


def can_edit(user: User, character: Character) -> bool:
    """Le propriétaire modifie sa fiche. Un PNJ, n'appartenant à personne, est à l'équipe qui les gère."""
    if character.is_npc:
        return can(user, Capability.MANAGE_NPCS)
    return character.user_id == user.id


def load_character(
    session: Session, character_id: int, viewer: User | None
) -> Character:
    """Une fiche visible pour cette personne, ou 404. Une fiche masquée reste invisible
    pour les autres : on ne confirme même pas qu'elle existe."""
    character = session.scalars(
        select(Character)
        .where(Character.id == character_id)
        .options(selectinload(Character.server), selectinload(Character.hangouts))
    ).one_or_none()
    if character is None:
        raise HTTPException(status_code=404, detail="Personnage introuvable")
    owner = viewer is not None and character.user_id == viewer.id
    if character.hidden_at is not None and not (
        owner or can(viewer, Capability.SEE_HIDDEN)
    ):
        raise HTTPException(status_code=404, detail="Personnage introuvable")
    return character


def present(
    character: Character, viewer: User | None
) -> CharacterOwnedOut | CharacterOut:
    """La fiche telle que cette personne a le droit de la voir."""
    if viewer is not None and character.user_id == viewer.id:
        return CharacterOwnedOut.model_validate(character)
    if can(viewer, Capability.SEE_OWNER):
        return CharacterOwnedOut.model_validate(character).model_copy(
            update={"is_mine": False}
        )
    return CharacterOut.model_validate(character)


def check_server_and_class(
    session: Session, server_id: int | None, character_class
) -> None:
    if server_id is None:
        return
    server = session.get(GameServer, server_id)
    if server is None or not server.is_active:
        raise field_error("server_id", "Ce serveur n'existe pas, ou plus")
    if character_class is not None and not is_available(character_class, server.game):
        raise field_error("class", "Cette classe n'existe pas dans ce jeu")


def move_to_server(
    session: Session, character: Character, server_id: int | None
) -> None:
    """Un déménagement : vers un serveur ouvert, et sans changer de jeu."""
    if character.is_npc:
        raise field_error("server_id", "Un PNJ n'a pas de serveur")
    if server_id is None:
        raise field_error("server_id", "Un personnage a toujours un serveur")
    target = session.get(GameServer, server_id)
    if target is None or not target.is_active:
        raise field_error("server_id", "Ce serveur n'existe pas, ou plus")
    current = session.get(GameServer, character.server_id)
    if current is not None and target.game != current.game:
        raise field_error("server_id", "Un personnage ne change pas de jeu")


@router.get("/{character_id}")
def read_character(
    character_id: int, session: SessionDep, viewer: OptionalUser
) -> CharacterOwnedOut | CharacterOut:
    shown = present(load_character(session, character_id, viewer), viewer)
    if viewer is not None and session.get(IgnoredCharacter, (viewer.id, character_id)):
        shown = shown.model_copy(update={"ignored": True})
    return shown


@router.post("", status_code=201)
def create_character(
    data: CharacterCreate, user: CurrentUser, session: SessionDep, response: Response
) -> CharacterOwnedOut:
    if data.is_npc and not can(user, Capability.MANAGE_NPCS):
        raise HTTPException(status_code=403, detail="Seule l'équipe crée des PNJ")
    check_server_and_class(session, data.server_id, data.class_)

    values = data.model_dump(exclude_none=True)
    if not data.is_npc:
        count, last = session.execute(
            select(func.count(), func.max(Character.position)).where(
                Character.user_id == user.id
            )
        ).one()
        if count >= MAX_CHARACTERS:
            raise HTTPException(
                status_code=409,
                detail=f"{MAX_CHARACTERS} personnages au plus par compte",
            )
        # Le nouveau venu se range au bout de la barre.
        values["position"] = (last or 0) + 1
    character = Character(user_id=None if data.is_npc else user.id, **values)
    session.add(character)
    session.commit()
    response.headers["Location"] = f"/api/characters/{character.id}"
    return CharacterOwnedOut.model_validate(load_character(session, character.id, user))


@router.patch("/{character_id}")
def update_character(
    character_id: int, data: CharacterUpdate, user: CurrentUser, session: SessionDep
) -> CharacterOwnedOut:
    character = load_character(session, character_id, user)
    if not can_edit(user, character):
        raise HTTPException(status_code=403, detail="Ce n'est pas ton personnage")

    changes = data.model_dump(exclude_unset=True)
    # Garder son serveur n'est jamais vérifié : même fermé, il ne doit pas bloquer la fiche.
    if changes.get("server_id", character.server_id) == character.server_id:
        changes.pop("server_id", None)
    if "server_id" in changes:
        move_to_server(session, character, changes["server_id"])
    if "class_" in changes or "server_id" in changes:
        target = session.get(GameServer, changes.get("server_id", character.server_id))
        character_class = changes.get("class_", character.class_)
        if (
            target
            and character_class
            and not is_available(character_class, target.game)
        ):
            raise field_error("class", "Cette classe n'existe pas dans ce jeu")

    inactive = changes.pop("inactive", None)
    note = changes.pop("inactive_note", None)
    if inactive is True:
        character.inactive_at = character.inactive_at or datetime.now(UTC)
        character.inactive_note = note
    elif inactive is False:
        # Revenir efface la raison du retrait.
        character.inactive_at = None
        character.inactive_note = None
    elif "inactive_note" in data.model_fields_set and character.inactive_at is not None:
        character.inactive_note = note

    # null vide un champ facultatif. Le genre revient alors à neutre, les horaires à vide.
    defaults = {"gender": "neutral", "play_days": [], "play_periods": []}
    for field, value in changes.items():
        setattr(character, field, defaults.get(field) if value is None else value)

    session.commit()
    return CharacterOwnedOut.model_validate(load_character(session, character.id, user))


@router.delete("/{character_id}", status_code=204)
def delete_character(character_id: int, user: CurrentUser, session: SessionDep) -> None:
    character = load_character(session, character_id, user)
    if not (can_edit(user, character) or can(user, Capability.DELETE_ANY)):
        raise HTTPException(status_code=403, detail="Ce n'est pas ton personnage")
    session.delete(character)
    session.commit()


me_router = APIRouter(prefix="/me", tags=["characters"])


def my_characters(session: Session, user: User) -> MyCharacters:
    characters = session.scalars(
        select(Character)
        .where(Character.user_id == user.id)
        .options(selectinload(Character.server))
        # Ceux qu'on ne joue pas en ce moment (en retrait, ou masqués) passent à la fin.
        .order_by(
            or_(Character.inactive_at.is_not(None), Character.hidden_at.is_not(None)),
            Character.position,
            Character.name,
            Character.id,
        )
    )
    return MyCharacters(
        items=[CharacterOwnedSummary.model_validate(c) for c in characters]
    )


@me_router.get("/characters")
def list_my_characters(user: CurrentUser, session: SessionDep) -> MyCharacters:
    return my_characters(session, user)


@me_router.put("/characters/order")
def order_my_characters(
    order: CharacterOrder, user: CurrentUser, session: SessionDep
) -> MyCharacters:
    """Ranger ses personnages : la liste doit les contenir tous, chacun une fois."""
    characters = {
        c.id: c
        for c in session.scalars(select(Character).where(Character.user_id == user.id))
    }
    if set(order.ids) != characters.keys():
        raise field_error("ids", "La liste doit contenir tous tes personnages")
    for position, character_id in enumerate(order.ids, start=1):
        characters[character_id].position = position
    session.commit()
    return my_characters(session, user)


MAX_HANGOUTS = 3


@router.put("/{character_id}/hangouts")
def replace_hangouts(
    character_id: int,
    hangouts: list[HangoutIn],
    user: CurrentUser,
    session: SessionDep,
) -> list[HangoutOut]:
    character = load_character(session, character_id, user)
    if not can_edit(user, character):
        raise HTTPException(status_code=403, detail="Ce n'est pas ton personnage")
    if len(hangouts) > MAX_HANGOUTS:
        raise HTTPException(
            status_code=409, detail=f"{MAX_HANGOUTS} lieux au plus par personnage"
        )
    places = [(h.area.strip().lower(), h.x, h.y) for h in hangouts]
    if len(set(places)) != len(places):
        raise field_error("hangouts", "Le même lieu apparaît deux fois")

    # On remplace d'un bloc : l'ancienne liste part, la nouvelle arrive.
    session.execute(
        delete(CharacterHangout).where(CharacterHangout.character_id == character.id)
    )
    session.flush()
    saved = [
        CharacterHangout(character_id=character.id, **h.model_dump()) for h in hangouts
    ]
    session.add_all(saved)
    session.commit()
    return [HangoutOut.model_validate(h) for h in saved]
