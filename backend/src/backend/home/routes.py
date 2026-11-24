from fastapi import APIRouter
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from backend.accounts.models import User
from backend.accounts.sessions import OptionalUser
from backend.characters.models import Character, CharacterHangout
from backend.characters.schemas import CharacterSummary
from backend.db import SessionDep
from backend.home import clock
from backend.home.schemas import HomeOut, Overheard, RightNow
from backend.ignores.filters import not_ignored
from backend.servers.models import GameServer
from backend.servers.schemas import ServerOut

router = APIRouter(tags=["home"])

RECENT_COUNT = 6
TOP_PLACES = 2


def visible(viewer: User | None = None):
    """Les fiches qu'on montre : ni masquées, ni en retrait, ni ignorées par qui regarde."""
    return (
        Character.hidden_at.is_(None),
        Character.inactive_at.is_(None),
        not_ignored(viewer),
    )


def right_now(
    session: Session, server: GameServer, viewer: User | None = None
) -> RightNow:
    moment = clock.now_in_paris()
    day, period = moment.isoweekday(), clock.period_of(moment)
    here = select(Character.id).where(
        *visible(viewer),
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


def owner():
    """Qui tient ce personnage. Un PNJ, qui n'appartient à personne, compte pour lui-même."""
    return func.coalesce(Character.user_id, -Character.id)


def overheard(session: Session, viewer: User | None = None) -> Overheard | None:
    # Une réplique faite d'espaces ne dirait rien au comptoir.
    candidates = (*visible(viewer), func.trim(Character.hook) != "")
    # D'abord un joueur au hasard, puis une de ses répliques : celui qui a dix
    # personnages n'a pas dix fois plus de chances d'être entendu.
    someone = session.scalar(
        select(owner())
        .where(*candidates)
        .group_by(owner())
        .order_by(func.random())
        .limit(1)
    )
    if someone is None:
        return None
    character, server_name = session.execute(
        select(Character, GameServer.name)
        .outerjoin(GameServer, GameServer.id == Character.server_id)
        .where(*candidates, owner() == someone)
        .order_by(func.random())
        .limit(1)
    ).one()
    return Overheard(
        character_id=character.id,
        name=character.name,
        server=server_name,
        hook=character.hook,
    )


@router.get("/home")
def home(
    session: SessionDep, viewer: OptionalUser, server_id: int | None = None
) -> HomeOut:
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

    # Un seul personnage par joueur, son plus récent : six créations d'affilée
    # ne remplissent pas toute la rangée. Rien ne montre qu'ils ont le même joueur.
    newest_first = (Character.created_at.desc(), Character.id.desc())
    rank = func.row_number().over(partition_by=Character.user_id, order_by=newest_first)
    latest = (
        select(Character.id, rank.label("rank"))
        .where(*visible(viewer), Character.is_npc.is_(False))
        .subquery()
    )
    recent = session.scalars(
        select(Character)
        .join(latest, latest.c.id == Character.id)
        .where(latest.c.rank == 1)
        .options(selectinload(Character.server))
        .order_by(*newest_first)
        .limit(RECENT_COUNT)
    )
    return HomeOut(
        right_now=right_now(session, server, viewer) if server else None,
        overheard=overheard(session, viewer),
        recent=[CharacterSummary.model_validate(c) for c in recent],
    )


@router.get("/home/overheard")
def another_overheard(session: SessionDep, viewer: OptionalUser) -> Overheard | None:
    """Une autre réplique, pour le bouton « Une autre »."""
    return overheard(session, viewer)
