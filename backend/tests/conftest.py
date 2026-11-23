from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.accounts.models import User
from backend.db import engine, get_session
from backend.main import app
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


@pytest.fixture
def client(session: Session) -> Iterator[TestClient]:
    app.dependency_overrides[get_session] = lambda: session
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def user(session: Session) -> User:
    user = User(email="joueur.test@example.com", password_hash="pas-un-vrai-hash")
    session.add(user)
    session.flush()
    return user


@pytest.fixture
def server(session: Session) -> GameServer:
    server = GameServer(game="dofus", name="Serveur de test")
    session.add(server)
    session.flush()
    return server
