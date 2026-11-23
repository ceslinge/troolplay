from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.accounts.models import (
    EmailToken,
    LoginFailure,
    ThrottleEvent,
    User,
    UserSession,
)
from backend.characters.models import Character, CharacterHangout
from backend.servers.models import GameServer


def log_in(client: TestClient, email: str, password: str):
    return client.post("/session", json={"email": email, "password": password})


def delete_account(client: TestClient, password: str):
    return client.request("DELETE", "/me", json={"password": password})


def count(session: Session, model, *conditions) -> int:
    return (
        session.scalar(select(func.count()).select_from(model).where(*conditions)) or 0
    )


def test_deleting_needs_the_password(
    session: Session, client: TestClient, member: User, member_password: str
) -> None:
    log_in(client, member.email, member_password)

    response = delete_account(client, "pas le bon")

    assert response.status_code == 403
    assert session.get(User, member.id) is not None


def test_deleting_removes_the_account_and_everything_it_owns(
    session: Session,
    client: TestClient,
    member: User,
    member_password: str,
    server: GameServer,
    outbox: list,
) -> None:
    character = Character(user_id=member.id, server_id=server.id, name="Partante")
    session.add(character)
    session.flush()
    session.add(CharacterHangout(character_id=character.id, area="Astrub", x=5, y=-18))
    session.flush()
    user_id, character_id = member.id, character.id
    client.post("/password/forgot", json={"email": member.email})
    log_in(client, member.email, "un essai raté")
    log_in(client, member.email, member_password)

    response = delete_account(client, member_password)

    assert response.status_code == 204
    session.expire_all()
    assert session.get(User, user_id) is None
    assert session.get(Character, character_id) is None
    assert (
        count(session, CharacterHangout, CharacterHangout.character_id == character_id)
        == 0
    )
    assert count(session, UserSession, UserSession.user_id == user_id) == 0
    assert count(session, EmailToken, EmailToken.user_id == user_id) == 0
    assert (
        count(session, LoginFailure, LoginFailure.email == "membre.test@example.com")
        == 0
    )
    assert (
        count(session, ThrottleEvent, ThrottleEvent.key == "membre.test@example.com")
        == 0
    )


def test_after_deleting_you_are_logged_out_for_good(
    client: TestClient, member: User, member_password: str
) -> None:
    log_in(client, member.email, member_password)

    response = delete_account(client, member_password)

    assert "session=" in response.headers["set-cookie"]
    assert client.get("/me").status_code == 401
    assert log_in(client, member.email, member_password).status_code == 401


def test_deleting_needs_a_session(client: TestClient, member_password: str) -> None:
    assert delete_account(client, member_password).status_code == 401
