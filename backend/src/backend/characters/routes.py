from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Response
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from backend.accounts.models import User
from backend.accounts.sessions import CurrentUser, OptionalUser
from backend.characters.classes import CharacterClass, is_available
from backend.characters.models import Character
from backend.characters.schemas import (
    CharacterCreate,
    CharacterList,
    CharacterOut,
    CharacterOwnedOut,
    CharacterOwnedSummary,
    CharacterSummary,
    CharacterUpdate,
    MyCharacters,
    Period,
)
from backend.db import SessionDep
from backend.servers.models import GameServer

router = APIRouter(prefix="/characters", tags=["characters"])


@router.get("")
def list_characters(
    session: SessionDep,
    server_id: int,
    day: Annotated[int | None, Query(ge=1, le=7)] = None,
    period: Period | None = None,
    character_class: Annotated[CharacterClass | None, Query(alias="class")] = None,
    include_inactive: bool = False,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> CharacterList:
    if session.get(GameServer, server_id) is None:
        raise HTTPException(status_code=404, detail="Serveur introuvable")

    query = select(Character).where(
        Character.server_id == server_id, Character.hidden_at.is_(None)
    )
    if day is not None:
        query = query.where(Character.play_days.contains([day]))
    if period is not None:
        query = query.where(Character.play_periods.contains([period]))
    if character_class is not None:
        query = query.where(Character.class_ == character_class)
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


def field_error(field: str, message: str) -> HTTPException:
    """Une erreur 422 sur un champ, dans le même format que celles de FastAPI."""
    return HTTPException(
        status_code=422,
        detail=[{"loc": ["body", field], "type": "value_error", "msg": message}],
    )


def is_staff(user: User | None) -> bool:
    return user is not None and user.role in ("moderator", "admin")


def can_edit(user: User, character: Character) -> bool:
    """Le propriétaire modifie sa fiche. Un PNJ, n'appartenant à personne, est aux admins."""
    if character.is_npc:
        return user.role == "admin"
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
    if character.hidden_at is not None and not (owner or is_staff(viewer)):
        raise HTTPException(status_code=404, detail="Personnage introuvable")
    return character


def present(
    character: Character, viewer: User | None
) -> CharacterOwnedOut | CharacterOut:
    """La fiche telle que cette personne a le droit de la voir."""
    if viewer is not None and character.user_id == viewer.id:
        return CharacterOwnedOut.model_validate(character)
    if is_staff(viewer):
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


@router.get("/{character_id}")
def read_character(
    character_id: int, session: SessionDep, viewer: OptionalUser
) -> CharacterOwnedOut | CharacterOut:
    return present(load_character(session, character_id, viewer), viewer)


@router.post("", status_code=201)
def create_character(
    data: CharacterCreate, user: CurrentUser, session: SessionDep, response: Response
) -> CharacterOwnedOut:
    if data.is_npc and user.role != "admin":
        raise HTTPException(status_code=403, detail="Seuls les admins créent des PNJ")
    check_server_and_class(session, data.server_id, data.class_)

    values = data.model_dump(exclude_none=True)
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
    if "class_" in changes:
        check_server_and_class(session, character.server_id, changes["class_"])

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
    if not (can_edit(user, character) or user.role == "admin"):
        raise HTTPException(status_code=403, detail="Ce n'est pas ton personnage")
    session.delete(character)
    session.commit()


me_router = APIRouter(prefix="/me", tags=["characters"])


@me_router.get("/characters")
def list_my_characters(user: CurrentUser, session: SessionDep) -> MyCharacters:
    characters = session.scalars(
        select(Character)
        .where(Character.user_id == user.id)
        .options(selectinload(Character.server))
        .order_by(Character.name, Character.id)
    )
    return MyCharacters(
        items=[CharacterOwnedSummary.model_validate(c) for c in characters]
    )
