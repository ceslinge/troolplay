import re
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.accounts.models import EmailToken, User

EMAIL = "nouveau.test@example.com"
PASSWORD = "une phrase de passe assez longue"


def sign_up(client: TestClient, email: str = EMAIL, **changes: object):
    body = {
        "email": email,
        "password": PASSWORD,
        "accept_rules": True,
        "age_confirmed": True,
    } | changes
    return client.post("/accounts", json=body)


def link_token(email: dict[str, str]) -> str:
    match = re.search(r"jeton=([\w-]+)", email["body"])
    assert match, "pas de lien dans l'email"
    return match.group(1)


def test_signing_up_creates_an_unverified_account(
    session: Session, client: TestClient, outbox: list
) -> None:
    response = sign_up(client)

    assert response.status_code == 202
    user = session.scalars(select(User).where(User.email == EMAIL)).one()
    assert user.email_verified_at is None
    assert user.password_hash != PASSWORD
    assert len(outbox) == 1
    assert outbox[0]["to"] == EMAIL


def test_the_full_journey_ends_logged_in(client: TestClient, outbox: list) -> None:
    sign_up(client)
    assert (
        client.post("/session", json={"email": EMAIL, "password": PASSWORD}).status_code
        == 403
    )

    verified = client.post("/accounts/verify", json={"token": link_token(outbox[0])})
    logged_in = client.post("/session", json={"email": EMAIL, "password": PASSWORD})

    assert verified.status_code == 204
    assert logged_in.status_code == 204
    assert client.get("/me").json()["email"] == EMAIL


def test_a_taken_address_gets_the_same_answer_and_its_owner_is_warned(
    session: Session, client: TestClient, outbox: list
) -> None:
    sign_up(client)
    client.post("/accounts/verify", json={"token": link_token(outbox[0])})

    first = sign_up(client, password="un autre mot de passe long")
    fresh = sign_up(client, email="encore.libre.test@example.com")

    assert first.status_code == fresh.status_code == 202
    assert first.json() == fresh.json()
    warning = outbox[1]
    assert warning["to"] == EMAIL
    assert "jeton=" not in warning["body"]


def test_signing_up_again_does_not_change_the_password(
    session: Session, client: TestClient, outbox: list
) -> None:
    sign_up(client)
    before = session.scalars(
        select(User.password_hash).where(User.email == EMAIL)
    ).one()

    sign_up(client, password="un autre mot de passe long")

    after = session.scalars(select(User.password_hash).where(User.email == EMAIL)).one()
    assert after == before


def test_a_link_works_only_once(client: TestClient, outbox: list) -> None:
    sign_up(client)
    token = link_token(outbox[0])

    assert client.post("/accounts/verify", json={"token": token}).status_code == 204
    assert client.post("/accounts/verify", json={"token": token}).status_code == 400


def test_an_expired_link_is_refused(
    session: Session, client: TestClient, outbox: list
) -> None:
    sign_up(client)
    for token in session.scalars(select(EmailToken)):
        token.expires_at = datetime.now(UTC) - timedelta(minutes=1)
    session.flush()

    response = client.post("/accounts/verify", json={"token": link_token(outbox[0])})

    assert response.status_code == 400


def test_a_new_link_can_be_requested(client: TestClient, outbox: list) -> None:
    sign_up(client)

    response = client.post("/accounts/verify/resend", json={"email": EMAIL})

    assert response.status_code == 202
    assert len(outbox) == 2
    assert (
        client.post(
            "/accounts/verify", json={"token": link_token(outbox[1])}
        ).status_code
        == 204
    )


def test_asking_a_link_for_an_unknown_address_reveals_nothing(
    client: TestClient, outbox: list
) -> None:
    unknown = client.post(
        "/accounts/verify/resend", json={"email": "inconnu.test@example.com"}
    )

    assert unknown.status_code == 202
    assert outbox == []


@pytest.mark.parametrize(
    "changes",
    [
        {"accept_rules": False},
        {"age_confirmed": False},
        {"password": "court"},
        {"password": "x" * 129},
        {"email": "pas-une-adresse"},
    ],
)
def test_invalid_signups_are_refused(
    client: TestClient, outbox: list, changes: dict
) -> None:
    assert sign_up(client, **changes).status_code == 422
    assert outbox == []


def test_signups_from_one_address_are_limited(client: TestClient, outbox: list) -> None:
    for number in range(5):
        assert (
            sign_up(client, email=f"serie{number}.test@example.com").status_code == 202
        )

    blocked = sign_up(client, email="une.de.trop.test@example.com")

    assert blocked.status_code == 429
    assert int(blocked.headers["retry-after"]) > 0
