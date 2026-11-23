import re
from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.accounts.models import EmailToken, User
from backend.main import app

NEW_PASSWORD = "une toute nouvelle phrase de passe"


def link_token(email: dict[str, str]) -> str:
    match = re.search(r"jeton=([\w-]+)", email["body"])
    assert match, "pas de lien dans l'email"
    return match.group(1)


def log_in(client: TestClient, email: str, password: str):
    return client.post("/session", json={"email": email, "password": password})


def forgot(client: TestClient, email: str):
    return client.post("/password/forgot", json={"email": email})


def test_forgetting_sends_a_link_to_the_owner(
    client: TestClient, member: User, outbox: list
) -> None:
    response = forgot(client, member.email)

    assert response.status_code == 202
    assert len(outbox) == 1
    assert outbox[0]["to"] == member.email


def test_an_unknown_address_gets_the_same_answer_and_no_email(
    client: TestClient, member: User, outbox: list
) -> None:
    known = forgot(client, member.email)
    unknown = forgot(client, "inconnu.test@example.com")

    assert known.status_code == unknown.status_code == 202
    assert known.json() == unknown.json()
    assert [email["to"] for email in outbox] == [member.email]


def test_resetting_replaces_the_password(
    client: TestClient, member: User, member_password: str, outbox: list
) -> None:
    forgot(client, member.email)

    reset = client.post(
        "/password/reset",
        json={"token": link_token(outbox[0]), "password": NEW_PASSWORD},
    )

    assert reset.status_code == 204
    assert log_in(client, member.email, member_password).status_code == 401
    assert log_in(client, member.email, NEW_PASSWORD).status_code == 204


def test_resetting_logs_out_everywhere(
    client: TestClient, member: User, member_password: str, outbox: list
) -> None:
    log_in(client, member.email, member_password)
    assert client.get("/me").status_code == 200

    forgot(client, member.email)
    with TestClient(app) as elsewhere:
        elsewhere.post(
            "/password/reset",
            json={"token": link_token(outbox[0]), "password": NEW_PASSWORD},
        )

    assert client.get("/me").status_code == 401


def test_a_reset_link_works_once_and_cancels_older_links(
    client: TestClient, member: User, outbox: list
) -> None:
    forgot(client, member.email)
    forgot(client, member.email)
    older, newer = link_token(outbox[0]), link_token(outbox[1])

    first = client.post(
        "/password/reset", json={"token": newer, "password": NEW_PASSWORD}
    )
    again = client.post(
        "/password/reset", json={"token": newer, "password": NEW_PASSWORD}
    )
    stale = client.post(
        "/password/reset", json={"token": older, "password": NEW_PASSWORD}
    )

    assert first.status_code == 204
    assert again.status_code == 400
    assert stale.status_code == 400


def test_a_reset_link_expires_after_an_hour(
    session: Session, client: TestClient, member: User, outbox: list
) -> None:
    forgot(client, member.email)
    for token in session.scalars(select(EmailToken)):
        token.expires_at = datetime.now(UTC) - timedelta(minutes=1)
    session.flush()

    response = client.post(
        "/password/reset",
        json={"token": link_token(outbox[0]), "password": NEW_PASSWORD},
    )

    assert response.status_code == 400


def test_a_too_short_new_password_is_refused(
    client: TestClient, member: User, outbox: list
) -> None:
    forgot(client, member.email)

    response = client.post(
        "/password/reset", json={"token": link_token(outbox[0]), "password": "court"}
    )

    assert response.status_code == 422


def test_forgotten_password_requests_are_limited(
    client: TestClient, member: User, outbox: list
) -> None:
    for _ in range(3):
        assert forgot(client, member.email).status_code == 202

    assert forgot(client, member.email).status_code == 429


def test_changing_needs_the_current_password(
    client: TestClient, member: User, member_password: str
) -> None:
    log_in(client, member.email, member_password)

    wrong = client.patch(
        "/me/password",
        json={"current_password": "pas le bon", "new_password": NEW_PASSWORD},
    )

    assert wrong.status_code == 403
    assert log_in(client, member.email, member_password).status_code == 204


def test_changing_keeps_this_session_and_closes_the_others(
    client: TestClient, member: User, member_password: str
) -> None:
    with TestClient(app) as elsewhere:
        log_in(elsewhere, member.email, member_password)
        log_in(client, member.email, member_password)

        changed = client.patch(
            "/me/password",
            json={"current_password": member_password, "new_password": NEW_PASSWORD},
        )

        assert changed.status_code == 204
        assert client.get("/me").status_code == 200
        assert elsewhere.get("/me").status_code == 401


def test_changing_needs_a_session(client: TestClient) -> None:
    response = client.patch(
        "/me/password",
        json={"current_password": "peu importe", "new_password": NEW_PASSWORD},
    )

    assert response.status_code == 401
