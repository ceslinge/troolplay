from collections.abc import Callable, Iterator
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


@pytest.fixture
def make_member(session: Session, member_password: str) -> Callable[..., User]:
    """Fabrique un compte vérifié, avec le mot de passe des tests."""

    def make(email: str, role: str = "user") -> User:
        user = User(
            email=email,
            password_hash=hash_password(member_password),
            email_verified_at=datetime.now(UTC),
            role=role,
        )
        session.add(user)
        session.flush()
        return user

    return make


@pytest.fixture
def log_in_as(member_password: str) -> Callable[[TestClient, User], TestClient]:
    def log_in(client: TestClient, user: User) -> TestClient:
        response = client.post(
            "/session", json={"email": user.email, "password": member_password}
        )
        assert response.status_code == 204
        return client

    return log_in


@pytest.fixture
def owner(make_member: Callable[..., User]) -> User:
    return make_member("proprietaire.test@example.com")


@pytest.fixture
def me(client: TestClient, owner: User, log_in_as) -> TestClient:
    """Le client, connecté en tant que propriétaire."""
    return log_in_as(client, owner)


@pytest.fixture
def stranger(client: TestClient, make_member, log_in_as) -> Iterator[TestClient]:
    """Un autre membre, connecté dans son propre navigateur."""
    with TestClient(app) as other:
        yield log_in_as(other, make_member("voisin.test@example.com"))


@pytest.fixture
def admin(client: TestClient, make_member, log_in_as) -> Iterator[TestClient]:
    with TestClient(app) as other:
        yield log_in_as(other, make_member("admin.test@example.com", role="admin"))


@pytest.fixture
def mine(me: TestClient, server: GameServer) -> int:
    """Un personnage du propriétaire."""
    response = me.post("/characters", json={"name": "Maëlis", "server_id": server.id})
    assert response.status_code == 201
    return response.json()["id"]
