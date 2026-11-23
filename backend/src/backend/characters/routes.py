from typing import Annotated

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from backend.characters.classes import CharacterClass
from backend.characters.models import Character
from backend.characters.schemas import (
    CharacterList,
    CharacterOut,
    CharacterSummary,
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
