from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.accounts.models import User
from backend.characters.models import Character
from backend.servers.models import GameServer


@pytest.fixture
def directory(session: Session, user: User, server: GameServer) -> GameServer:
    """Un serveur de test et quelques habitués, tous au même compte."""
    other = GameServer(game="dofus", name="Autre serveur de test")
    session.add(other)
    session.flush()
    session.add_all(
        [
            Character(
                user_id=user.id,
                server_id=server.id,
                name="Bruyère",
                class_="sadida",
                play_days=[6],
                play_periods=["afternoon"],
            ),
            Character(
                user_id=user.id,
                server_id=server.id,
                name="Aldegonde",
                class_="feca",
                play_days=[1, 2],
                play_periods=["morning"],
            ),
            Character(
                user_id=user.id,
                server_id=server.id,
                name="Cendre",
                class_="feca",
                play_days=[6],
                play_periods=["evening"],
                inactive_at=datetime.now(UTC),
            ),
            Character(
                user_id=user.id,
                server_id=server.id,
                name="Discrète",
                hidden_at=datetime.now(UTC),
            ),
            Character(user_id=user.id, server_id=other.id, name="Ailleurs"),
        ]
    )
    session.flush()
    return server


def names(client: TestClient, server: GameServer, **params: object) -> list[str]:
    response = client.get("/characters", params={"server_id": server.id, **params})
    assert response.status_code == 200
    return [character["name"] for character in response.json()["items"]]


def test_a_server_lists_its_active_characters_by_name(
    client: TestClient, directory: GameServer
) -> None:
    assert names(client, directory) == ["Aldegonde", "Bruyère"]


def test_inactive_characters_can_be_included(
    client: TestClient, directory: GameServer
) -> None:
    assert names(client, directory, include_inactive=True) == [
        "Aldegonde",
        "Bruyère",
        "Cendre",
    ]


@pytest.mark.parametrize(
    ("params", "expected"),
    [
        ({"day": 6}, ["Bruyère"]),
        ({"period": "morning"}, ["Aldegonde"]),
        ({"class": "feca"}, ["Aldegonde"]),
        ({"class": "feca", "include_inactive": True}, ["Aldegonde", "Cendre"]),
        ({"day": 6, "period": "morning"}, []),
    ],
)
def test_filters_combine(
    client: TestClient, directory: GameServer, params: dict, expected: list[str]
) -> None:
    assert names(client, directory, **params) == expected


def test_pagination_keeps_the_total(client: TestClient, directory: GameServer) -> None:
    response = client.get(
        "/characters", params={"server_id": directory.id, "limit": 1, "offset": 1}
    )

    body = response.json()
    assert [c["name"] for c in body["items"]] == ["Bruyère"]
    assert body["total"] == 2


def test_the_list_never_reveals_owners(
    client: TestClient, directory: GameServer, user: User
) -> None:
    response = client.get("/characters", params={"server_id": directory.id})

    assert "user_id" not in response.text
    assert user.email not in response.text


def test_an_unknown_server_is_not_found(client: TestClient) -> None:
    response = client.get("/characters", params={"server_id": 999999999})

    assert response.status_code == 404


@pytest.mark.parametrize(
    "params",
    [{"day": 8}, {"period": "midi"}, {"class": "Crâ"}, {"limit": 500}, {}],
)
def test_invalid_parameters_are_refused(
    client: TestClient, directory: GameServer, params: dict
) -> None:
    query = {"server_id": directory.id, **params} if params else {}
    response = client.get("/characters", params=query)

    assert response.status_code == 422
