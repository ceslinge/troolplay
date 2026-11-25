"""Les serveurs depuis l'Espace équipe (#81) : ajouter, renommer, fermer, rouvrir.

Réservé aux admins. Fermer n'efface rien : les fiches et les histoires d'un serveur fermé
restent lisibles, on n'y crée simplement plus de personnage. Chaque geste va au journal.
"""

from typing import Annotated

from fastapi import APIRouter, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.accounts.models import User
from backend.accounts.roles import Capability, require
from backend.characters.models import Character
from backend.characters.routes import field_error
from backend.db import SessionDep
from backend.moderation.team import log
from backend.servers.models import GameServer
from backend.servers.schemas import (
    ServerCreate,
    ServerRename,
    ServerWhy,
    TeamServer,
    TeamServerList,
)
from backend.stories.models import Story

router = APIRouter(prefix="/moderation/servers", tags=["moderation"])

ServerKeeper = Annotated[User, require(Capability.MANAGE_SERVERS)]


def counted(session: Session, server: GameServer) -> TeamServer:
    characters = session.scalar(
        select(func.count()).where(Character.server_id == server.id)
    )
    stories = session.scalar(
        select(func.count())
        .select_from(Story)
        .join(Story.character)
        .where(Character.server_id == server.id, Story.published_at.is_not(None))
    )
    return TeamServer.model_validate(
        {
            "id": server.id,
            "game": server.game,
            "name": server.name,
            "is_active": server.is_active,
            "characters": characters or 0,
            "stories": stories or 0,
        }
    )


def load_server(session: Session, server_id: int) -> GameServer:
    server = session.get(GameServer, server_id)
    if server is None:
        raise HTTPException(status_code=404, detail="Serveur introuvable")
    return server


def check_name_free(
    session: Session, game: str, name: str, but: int | None = None
) -> None:
    """Deux serveurs d'un même jeu ne portent pas le même nom, à la casse près."""
    taken = session.scalar(
        select(GameServer.id).where(
            GameServer.game == game,
            func.lower(GameServer.name) == name.lower(),
            GameServer.id != (but or 0),
        )
    )
    if taken is not None:
        raise field_error("name", "Un serveur de ce jeu porte déjà ce nom")


@router.get("")
def list_servers(session: SessionDep, _: ServerKeeper) -> TeamServerList:
    """Tous les serveurs, fermés compris, par jeu puis par nom."""
    servers = session.scalars(
        select(GameServer).order_by(GameServer.game, GameServer.name)
    )
    return TeamServerList(items=[counted(session, s) for s in servers])


@router.post("", status_code=201)
def add_server(
    data: ServerCreate, session: SessionDep, actor: ServerKeeper
) -> TeamServer:
    name = data.name.strip()
    check_name_free(session, data.game, name)
    server = GameServer(game=data.game, name=name)
    session.add(server)
    session.flush()
    log(session, actor, "add_server", data.reason, server_id=server.id)
    session.commit()
    return counted(session, server)


@router.patch("/{server_id}")
def rename_server(
    server_id: int, data: ServerRename, session: SessionDep, actor: ServerKeeper
) -> TeamServer:
    server = load_server(session, server_id)
    name = data.name.strip()
    if name == server.name:
        raise HTTPException(status_code=409, detail="C'est déjà son nom")
    check_name_free(session, server.game, name, but=server.id)
    before = server.name
    server.name = name
    log(
        session, actor, "rename_server", data.reason, server_id=server.id, detail=before
    )
    session.commit()
    return counted(session, server)


def set_open(
    session: Session, server: GameServer, actor: User, is_open: bool, reason: str
) -> TeamServer:
    if server.is_active == is_open:
        raise HTTPException(
            status_code=409,
            detail="Ce serveur est déjà ouvert"
            if is_open
            else "Ce serveur est déjà fermé",
        )
    server.is_active = is_open
    log(
        session,
        actor,
        "reopen_server" if is_open else "close_server",
        reason,
        server_id=server.id,
    )
    session.commit()
    return counted(session, server)


@router.post("/{server_id}/close")
def close_server(
    server_id: int, data: ServerWhy, session: SessionDep, actor: ServerKeeper
) -> TeamServer:
    return set_open(session, load_server(session, server_id), actor, False, data.reason)


@router.post("/{server_id}/reopen")
def reopen_server(
    server_id: int, data: ServerWhy, session: SessionDep, actor: ServerKeeper
) -> TeamServer:
    return set_open(session, load_server(session, server_id), actor, True, data.reason)
