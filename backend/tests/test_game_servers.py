import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.servers.models import GameServer


def test_write_and_read_a_server(session: Session) -> None:
    session.add(GameServer(game="dofus", name="Serveur de test"))
    session.flush()
    session.expunge_all()

    server = session.scalars(
        select(GameServer).where(GameServer.name == "Serveur de test")
    ).one()

    assert server.game == "dofus"
    assert server.is_active is True


def test_unknown_game_is_refused(session: Session) -> None:
    session.add(GameServer(game="wakfu", name="Serveur de test"))

    with pytest.raises(IntegrityError):
        session.flush()


def test_same_name_twice_in_a_game_is_refused(session: Session) -> None:
    session.add(GameServer(game="dofus", name="Serveur de test"))
    session.add(GameServer(game="dofus", name="Serveur de test"))

    with pytest.raises(IntegrityError):
        session.flush()
