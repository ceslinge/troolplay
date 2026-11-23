from collections.abc import Iterator

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.db import engine
from backend.servers.models import GameServer


@pytest.fixture
def session() -> Iterator[Session]:
    with engine.connect() as connection:
        transaction = connection.begin()
        with Session(
            bind=connection, join_transaction_mode="create_savepoint"
        ) as session:
            yield session
        transaction.rollback()


def test_write_and_read_a_server(session: Session) -> None:
    session.add(GameServer(game="dofus", name="Ombrelune"))
    session.flush()
    session.expunge_all()

    server = session.scalars(
        select(GameServer).where(GameServer.name == "Ombrelune")
    ).one()

    assert server.game == "dofus"
    assert server.is_active is True


def test_unknown_game_is_refused(session: Session) -> None:
    session.add(GameServer(game="wakfu", name="Ombrelune"))

    with pytest.raises(IntegrityError):
        session.flush()


def test_same_name_twice_in_a_game_is_refused(session: Session) -> None:
    session.add(GameServer(game="dofus", name="Ombrelune"))
    session.add(GameServer(game="dofus", name="Ombrelune"))

    with pytest.raises(IntegrityError):
        session.flush()
