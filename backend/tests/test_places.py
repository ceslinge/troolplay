from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.accounts.models import User
from backend.characters.models import Character, CharacterHangout
from backend.servers.models import GameServer


def add(
    session: Session,
    user: User,
    server: GameServer,
    name: str,
    places: list[tuple],
    **fields,
) -> Character:
    character = Character(user_id=user.id, server_id=server.id, name=name, **fields)
    session.add(character)
    session.flush()
    for area, x, y, label in places:
        session.add(
            CharacterHangout(
                character_id=character.id,
                area=area,
                x=x,
                y=y,
                label=label,
                habits=f"Habitude de {name}",
            )
        )
    session.flush()
    return character


def places(client: TestClient, server: GameServer, **params) -> list[dict]:
    response = client.get(f"/servers/{server.id}/places", params=params)
    assert response.status_code == 200
    return response.json()["items"]


@pytest.fixture
def map_of_test(session: Session, user: User, server: GameServer) -> GameServer:
    taverne = ("Astrub", 5, -18, "Taverne de test")
    add(
        session,
        user,
        server,
        "Alix",
        [taverne],
        play_days=[4],
        play_periods=["evening"],
    )
    add(
        session,
        user,
        server,
        "Bérénice",
        [("astrub ", 5, -18, "La taverne")],
        play_days=[6],
        play_periods=["evening"],
    )
    add(
        session,
        user,
        server,
        "Côme",
        [taverne, ("Bonta", -28, -56, None)],
        play_days=[4],
        play_periods=["morning"],
    )
    add(session, user, server, "Discrète", [taverne], hidden_at=datetime.now(UTC))
    add(session, user, server, "Partie", [taverne], inactive_at=datetime.now(UTC))
    return server


def test_places_gather_their_regulars_busiest_first(
    client: TestClient, map_of_test: GameServer
) -> None:
    items = places(client, map_of_test)

    assert [(p["area"], p["x"], p["y"]) for p in items] == [
        ("Astrub", 5, -18),
        ("Bonta", -28, -56),
    ]
    taverne = items[0]
    # Trois habitués : le même lieu, même écrit « astrub » avec un autre nom.
    assert [r["character"]["name"] for r in taverne["regulars"]] == [
        "Alix",
        "Bérénice",
        "Côme",
    ]
    assert taverne["label"] == "Taverne de test"
    assert taverne["regulars"][0]["habits"] == "Habitude de Alix"


def test_hidden_and_inactive_characters_are_left_out(
    client: TestClient, map_of_test: GameServer
) -> None:
    names = {
        r["character"]["name"]
        for p in places(client, map_of_test)
        for r in p["regulars"]
    }

    assert not {"Discrète", "Partie"} & names


@pytest.mark.parametrize(
    ("params", "expected"),
    [
        ({"day": 4}, {"Alix", "Côme"}),
        ({"period": "evening"}, {"Alix", "Bérénice"}),
        ({"day": 4, "period": "evening"}, {"Alix"}),
        ({"day": 7}, set()),
    ],
)
def test_places_follow_the_day_and_period(
    client: TestClient, map_of_test: GameServer, params: dict, expected: set
) -> None:
    names = {
        r["character"]["name"]
        for p in places(client, map_of_test, **params)
        for r in p["regulars"]
    }

    assert names == expected


def test_a_place_without_regulars_at_that_time_is_not_listed(
    client: TestClient, map_of_test: GameServer
) -> None:
    assert [p["area"] for p in places(client, map_of_test, period="evening")] == [
        "Astrub"
    ]


def test_an_unknown_server_is_not_found(client: TestClient) -> None:
    assert client.get("/servers/999999999/places").status_code == 404


@pytest.mark.parametrize("params", [{"day": 0}, {"period": "midi"}])
def test_invalid_filters_are_refused(
    client: TestClient, map_of_test: GameServer, params: dict
) -> None:
    assert (
        client.get(f"/servers/{map_of_test.id}/places", params=params).status_code
        == 422
    )


def test_places_never_reveal_owners(
    client: TestClient, map_of_test: GameServer, user: User
) -> None:
    response = client.get(f"/servers/{map_of_test.id}/places")

    assert "user_id" not in response.text
    assert user.email not in response.text
