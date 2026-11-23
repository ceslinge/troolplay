from collections.abc import Iterator
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.accounts.models import User
from backend.accounts.security import hash_password
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


@pytest.fixture
def outbox(monkeypatch: pytest.MonkeyPatch) -> list[dict[str, str]]:
    """Les emails « envoyés » pendant le test, au lieu du terminal."""
    sent: list[dict[str, str]] = []

    def capture(to: str, subject: str, body: str) -> None:
        sent.append({"to": to, "subject": subject, "body": body})

    monkeypatch.setattr("backend.accounts.emails.send_email", capture)
    return sent


@pytest.fixture
def member_password() -> str:
    return "une phrase de passe assez longue"


@pytest.fixture
def member(session: Session, member_password: str) -> User:
    """Un compte vérifié, avec un vrai mot de passe."""
    user = User(
        email="membre.test@example.com",
        password_hash=hash_password(member_password),
        email_verified_at=datetime.now(UTC),
    )
    session.add(user)
    session.flush()
    return user
