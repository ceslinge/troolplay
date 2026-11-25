from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.accounts.models import User, UserSession
from backend.accounts.security import token_hash


def log_in(client: TestClient, email: str, password: str):
    return client.post("/session", json={"email": email, "password": password})


def test_logging_in_opens_a_session(
    client: TestClient, member: User, member_password: str
) -> None:
    response = log_in(client, member.email, member_password)

    assert response.status_code == 204
    cookie = response.headers["set-cookie"]
    assert "session=" in cookie
    assert "HttpOnly" in cookie
    assert "SameSite=lax" in cookie
    assert client.get("/me").json()["email"] == member.email


def test_the_email_is_not_case_sensitive(
    client: TestClient, member: User, member_password: str
) -> None:
    assert log_in(client, member.email.upper(), member_password).status_code == 204


def test_the_database_only_keeps_a_fingerprint_of_the_token(
    session: Session, client: TestClient, member: User, member_password: str
) -> None:
    log_in(client, member.email, member_password)
    token = client.cookies["session"]

    stored = session.scalars(select(UserSession.token_hash)).all()
    assert token_hash(token) in stored
    assert token not in stored


def test_a_wrong_password_and_an_unknown_email_look_the_same(
    client: TestClient, member: User, member_password: str
) -> None:
    wrong_password = log_in(client, member.email, "pas le bon mot de passe")
    unknown_email = log_in(client, "personne.test@example.com", member_password)

    assert wrong_password.status_code == unknown_email.status_code == 401
    assert wrong_password.json() == unknown_email.json()


def test_an_unverified_account_cannot_log_in(
    session: Session, client: TestClient, member: User, member_password: str
) -> None:
    member.email_verified_at = None
    session.flush()

    assert log_in(client, member.email, member_password).status_code == 403


def test_a_banned_account_logs_in_only_to_read_and_contest(
    session: Session, client: TestClient, member: User, member_password: str
) -> None:
    member.banned_at = datetime.now(UTC)
    session.flush()

    # #141 : connecté pour contester, mais le reste du site lui reste fermé
    # (tests/test_suspended.py vérifie chaque route).
    assert log_in(client, member.email, member_password).status_code == 204
    assert client.get("/me").json()["suspended"] is True
    assert client.get("/me/characters").status_code == 401


def test_logging_out_closes_the_session_on_the_server(
    session: Session, client: TestClient, member: User, member_password: str
) -> None:
    log_in(client, member.email, member_password)
    token = client.cookies["session"]

    assert client.delete("/session").status_code == 204

    client.cookies.set("session", token)
    assert client.get("/me").status_code == 401


def test_me_needs_a_session(client: TestClient) -> None:
    assert client.get("/me").status_code == 401


def test_an_expired_session_is_refused(
    session: Session, client: TestClient, member: User, member_password: str
) -> None:
    log_in(client, member.email, member_password)
    for user_session in session.scalars(select(UserSession)):
        user_session.expires_at = datetime.now(UTC) - timedelta(minutes=1)
    session.flush()

    assert client.get("/me").status_code == 401


def test_too_many_failures_are_slowed_down(
    client: TestClient, member: User, member_password: str
) -> None:
    for _ in range(5):
        assert log_in(client, member.email, "pas le bon").status_code == 401

    blocked = log_in(client, member.email, member_password)

    assert blocked.status_code == 429
    assert int(blocked.headers["retry-after"]) > 0


def test_a_request_from_another_site_is_refused(
    client: TestClient, member: User, member_password: str
) -> None:
    response = client.post(
        "/session",
        json={"email": member.email, "password": member_password},
        headers={"Origin": "https://site-malveillant.example"},
    )

    assert response.status_code == 403


def test_a_request_from_the_site_itself_is_accepted(
    client: TestClient, member: User, member_password: str
) -> None:
    response = client.post(
        "/session",
        json={"email": member.email, "password": member_password},
        headers={"Origin": "http://localhost:5173"},
    )

    assert response.status_code == 204


def test_an_account_without_a_real_password_cannot_log_in(
    session: Session, client: TestClient, member: User
) -> None:
    member.password_hash = "!demo"
    session.flush()

    assert log_in(client, member.email, "!demo").status_code == 401
