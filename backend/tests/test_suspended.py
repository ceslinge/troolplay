"""Un compte suspendu se connecte, mais le site lui reste fermé (#141).

Garde-fou : sur chaque route de l'API, un compte suspendu reçoit la même réponse qu'un
visiteur, sauf sur les quelques routes qui lui sont ouvertes (SessionUser). Une route
ajoutée plus tard est vérifiée d'office.
"""

import re
from collections.abc import Iterator
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.accounts.models import User
from backend.main import app

# Ce qu'un compte suspendu peut faire : se voir, lire les décisions qui le visent,
# les contester, et se déconnecter. Rien d'autre.
OPEN_TO_SUSPENDED = {
    ("GET", "/me"),
    ("GET", "/me/decisions"),
    ("POST", "/me/decisions/{action_id}/contest"),
    ("DELETE", "/session"),
}


@pytest.fixture
def suspended(
    client: TestClient, session: Session, make_member, log_in_as
) -> Iterator[TestClient]:
    user: User = make_member("suspendu.test@example.com")
    with TestClient(app) as other:
        log_in_as(other, user)
        user.banned_at = datetime.now(UTC)
        session.flush()
        yield other


def every_route() -> list[tuple[str, str]]:
    routes = []
    for path, methods in app.openapi()["paths"].items():
        for method in methods:
            routes.append((method.upper(), path))
    return routes


def call(client: TestClient, method: str, path: str) -> int:
    url = re.sub(r"\{[^}]+\}", "1", path)
    body = {} if method in ("POST", "PUT", "PATCH") else None
    return client.request(method, url, json=body).status_code


def test_the_open_routes_still_exist() -> None:
    assert OPEN_TO_SUSPENDED <= set(every_route())


@pytest.mark.parametrize(
    ("method", "path"),
    [r for r in every_route() if r not in OPEN_TO_SUSPENDED],
    ids=lambda value: value,
)
def test_a_suspended_account_is_a_visitor_everywhere_else(
    client: TestClient, suspended: TestClient, method: str, path: str
) -> None:
    with TestClient(app) as visitor:
        expected = call(visitor, method, path)

    assert call(suspended, method, path) == expected


def test_a_suspended_account_sees_its_suspension(suspended: TestClient) -> None:
    me = suspended.get("/me").json()

    assert me["suspended"] is True
    assert me["suspended_until"] is None
    assert me["capabilities"] == []
    assert suspended.get("/me/decisions").status_code == 200
