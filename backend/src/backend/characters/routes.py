from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from backend.characters.models import Character
from backend.characters.schemas import CharacterOut
from backend.db import SessionDep

router = APIRouter(prefix="/characters", tags=["characters"])


@router.get("/{character_id}")
def read_character(character_id: int, session: SessionDep) -> CharacterOut:
    character = session.scalars(
        select(Character)
        .where(Character.id == character_id, Character.hidden_at.is_(None))
        .options(selectinload(Character.server), selectinload(Character.hangouts))
    ).one_or_none()
    if character is None:
        raise HTTPException(status_code=404, detail="Personnage introuvable")
    return CharacterOut.model_validate(character)
