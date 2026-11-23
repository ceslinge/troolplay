from fastapi import APIRouter
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from backend.characters.models import Character, CharacterHangout
from backend.characters.schemas import CharacterSummary
from backend.db import SessionDep
from backend.home import clock
from backend.home.schemas import HomeOut, Overheard, RightNow
from backend.servers.models import GameServer
from backend.servers.schemas import ServerOut

router = APIRouter(tags=["home"])

RECENT_COUNT = 6
TOP_PLACES = 2


def visible():
    """Les fiches qu'on montre à tout le monde : ni masquées, ni en retrait."""
    return (Character.hidden_at.is_(None), Character.inactive_at.is_(None))


def right_now(session: Session, server: GameServer) -> RightNow:
    moment = clock.now_in_paris()
    day, period = moment.isoweekday(), clock.period_of(moment)
    here = select(Character.id).where(
        *visible(),
        Character.server_id == server.id,
        Character.play_days.contains([day]),
        Character.play_periods.contains([period]),
    )
    count = session.scalar(select(func.count()).select_from(here.subquery())) or 0
    place = func.coalesce(CharacterHangout.label, CharacterHangout.area)
    places = session.scalars(
        select(place)
        .where(CharacterHangout.character_id.in_(here))
        .group_by(place)
        .order_by(func.count().desc(), place)
        .limit(TOP_PLACES)
    ).all()
    return RightNow(
        server=ServerOut.model_validate(server),
        day=day,
        period=period,
        count=count,
        places=list(places),
    )


def overheard(session: Session) -> Overheard | None:
    found = session.execute(
        select(Character, GameServer.name)
        .outerjoin(GameServer, GameServer.id == Character.server_id)
        # Une réplique faite d'espaces ne dirait rien au comptoir.
        .where(*visible(), func.trim(Character.hook) != "")
        .order_by(func.random())
        .limit(1)
    ).one_or_none()
    if found is None:
        return None
    character, server_name = found
    return Overheard(
        character_id=character.id,
        name=character.name,
        server=server_name,
        hook=character.hook,
    )


@router.get("/home")
def home(session: SessionDep, server_id: int | None = None) -> HomeOut:
    servers = select(GameServer).where(GameServer.is_active)
    # Un serveur retenu qui a fermé depuis ne doit pas casser l'accueil :
    # on retombe alors sur le premier serveur actif.
    chosen = (
        session.scalars(servers.where(GameServer.id == server_id)).one_or_none()
        if server_id is not None
        else None
    )
    server = (
        chosen
        or session.scalars(
            servers.order_by(GameServer.game, GameServer.name).limit(1)
        ).one_or_none()
    )

    recent = session.scalars(
        select(Character)
        .where(*visible(), Character.is_npc.is_(False))
        .options(selectinload(Character.server))
        .order_by(Character.created_at.desc(), Character.id.desc())
        .limit(RECENT_COUNT)
    )
    return HomeOut(
        right_now=right_now(session, server) if server else None,
        overheard=overheard(session),
        recent=[CharacterSummary.model_validate(c) for c in recent],
    )


@router.get("/home/overheard")
def another_overheard(session: SessionDep) -> Overheard | None:
    """Une autre réplique, pour le bouton « Une autre »."""
    return overheard(session)
