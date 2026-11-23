"""« Qui traîne ici ? » : les lieux d'un serveur, et les personnages qui ont l'habitude d'y être."""

from collections import Counter, defaultdict
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from backend.characters.models import Character, CharacterHangout
from backend.characters.schemas import CharacterSummary, Period
from backend.db import SessionDep
from backend.servers.models import GameServer

router = APIRouter(prefix="/servers", tags=["servers"])


class Regular(BaseModel):
    character: CharacterSummary
    habits: str | None


class Place(BaseModel):
    area: str
    x: int
    y: int
    label: str | None
    regulars: list[Regular]


class PlaceList(BaseModel):
    items: list[Place]


@router.get("/{server_id}/places")
def list_places(
    server_id: int,
    session: SessionDep,
    day: Annotated[int | None, Query(ge=1, le=7)] = None,
    period: Period | None = None,
) -> PlaceList:
    if session.get(GameServer, server_id) is None:
        raise HTTPException(status_code=404, detail="Serveur introuvable")

    query = (
        select(CharacterHangout, Character)
        .join(Character, Character.id == CharacterHangout.character_id)
        .where(
            Character.server_id == server_id,
            Character.hidden_at.is_(None),
            Character.inactive_at.is_(None),
        )
        .options(selectinload(Character.server))
        .order_by(Character.name, Character.id)
    )
    if day is not None:
        query = query.where(Character.play_days.contains([day]))
    if period is not None:
        query = query.where(Character.play_periods.contains([period]))

    # Un même lieu peut porter un nom un peu différent d'une fiche à l'autre :
    # on le reconnaît à sa zone et à ses coordonnées, et on garde le nom le plus donné.
    regulars: dict[tuple[str, int, int], list[Regular]] = defaultdict(list)
    labels: dict[tuple[str, int, int], Counter[str]] = defaultdict(Counter)
    areas: dict[tuple[str, int, int], str] = {}
    for hangout, character in session.execute(query):
        key = (hangout.area.strip().lower(), hangout.x, hangout.y)
        areas.setdefault(key, hangout.area.strip())
        if hangout.label:
            labels[key][hangout.label.strip()] += 1
        regulars[key].append(
            Regular(
                character=CharacterSummary.model_validate(character),
                habits=hangout.habits,
            )
        )

    places = [
        Place(
            area=areas[key],
            x=key[1],
            y=key[2],
            label=labels[key].most_common(1)[0][0] if labels[key] else None,
            regulars=people,
        )
        for key, people in regulars.items()
    ]
    # Les lieux les plus fréquentés d'abord.
    places.sort(key=lambda p: (-len(p.regulars), (p.label or p.area).lower()))
    return PlaceList(items=places)
