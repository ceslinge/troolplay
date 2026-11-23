from fastapi import APIRouter
from sqlalchemy import select

from backend.db import SessionDep
from backend.servers.models import GameServer
from backend.servers.schemas import ServerList, ServerOut

router = APIRouter(prefix="/servers", tags=["servers"])


@router.get("")
def list_servers(session: SessionDep) -> ServerList:
    servers = session.scalars(
        select(GameServer)
        .where(GameServer.is_active)
        .order_by(GameServer.game, GameServer.name)
    )
    return ServerList(items=[ServerOut.model_validate(s) for s in servers])
