from fastapi import APIRouter, Response
from pydantic import BaseModel
from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import selectinload

from backend.accounts.sessions import CurrentUser
from backend.characters.models import Character
from backend.characters.routes import load_character
from backend.characters.schemas import CharacterSummary
from backend.db import SessionDep
from backend.errors import field_error
from backend.ignores.models import IgnoredCharacter

router = APIRouter(prefix="/me/ignored", tags=["ignores"])


class IgnoredList(BaseModel):
    items: list[CharacterSummary]


@router.get("")
def list_ignored(user: CurrentUser, session: SessionDep) -> IgnoredList:
    """Mes personnages ignorés, le dernier ignoré d'abord."""
    characters = session.scalars(
        select(Character)
        .join(IgnoredCharacter, IgnoredCharacter.character_id == Character.id)
        .where(IgnoredCharacter.user_id == user.id)
        .options(selectinload(Character.server))
        .order_by(IgnoredCharacter.created_at.desc(), Character.id)
    )
    return IgnoredList(items=[CharacterSummary.model_validate(c) for c in characters])


@router.put("/{character_id}", status_code=204)
def ignore(character_id: int, user: CurrentUser, session: SessionDep) -> Response:
    """Ignorer un personnage. Le refaire ne change rien."""
    character = load_character(session, character_id, user)
    if character.user_id == user.id:
        raise field_error("character_id", "On n'ignore pas ses propres personnages")
    session.execute(
        insert(IgnoredCharacter)
        .values(user_id=user.id, character_id=character.id)
        .on_conflict_do_nothing()
    )
    session.commit()
    return Response(status_code=204)


@router.delete("/{character_id}", status_code=204)
def unignore(character_id: int, user: CurrentUser, session: SessionDep) -> Response:
    session.execute(
        delete(IgnoredCharacter).where(
            IgnoredCharacter.user_id == user.id,
            IgnoredCharacter.character_id == character_id,
        )
    )
    session.commit()
    return Response(status_code=204)
