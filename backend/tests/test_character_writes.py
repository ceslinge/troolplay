from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.characters.models import Character
from backend.servers.models import GameServer


@pytest.fixture
def retro(session: Session) -> GameServer:
    server = GameServer(game="retro", name="Serveur rétro de test")
    session.add(server)
    session.flush()
    return server


# Créer


def test_creating_needs_only_a_name_and_a_server(
    me: TestClient, server: GameServer
) -> None:
    response = me.post("/characters", json={"name": "Maëlis", "server_id": server.id})

    assert response.status_code == 201
    body = response.json()
    assert response.headers["location"] == f"/api/characters/{body['id']}"
    assert body["gender"] == "neutral"
    assert body["is_mine"] is True
    assert body["hidden"] is False
    assert "user_id" not in response.text


def test_creating_a_full_sheet(me: TestClient, server: GameServer) -> None:
    response = me.post(
        "/characters",
        json={
            "name": "Maëlis",
            "server_id": server.id,
            "gender": "feminine",
            "class": "cra",
            "level": 142,
            "hook": "Si c'est pour l'arc, il n'est pas à vendre.",
            "play_days": [1, 3, 5],
            "play_periods": ["evening"],
        },
    )

    body = response.json()
    assert body["class"] == "cra"
    assert body["play_days"] == [1, 3, 5]


def test_creating_needs_a_session(client: TestClient, server: GameServer) -> None:
    response = client.post(
        "/characters", json={"name": "Maëlis", "server_id": server.id}
    )

    assert response.status_code == 401


@pytest.mark.parametrize(
    "changes",
    [
        {"name": "M"},
        {"level": 0},
        {"gender": "iel"},
        {"class": "Crâ"},
        {"play_days": [8]},
        {"play_days": [1, 1]},
        {"hook": "x" * 201},
        {"user_id": 1},
        {"server_id": None},
    ],
)
def test_invalid_sheets_are_refused(
    me: TestClient, server: GameServer, changes: dict
) -> None:
    body = {"name": "Maëlis", "server_id": server.id} | changes
    assert me.post("/characters", json=body).status_code == 422


def test_a_class_must_exist_in_the_game_of_the_server(
    me: TestClient, retro: GameServer
) -> None:
    response = me.post(
        "/characters",
        json={"name": "Tobias", "server_id": retro.id, "class": "roublard"},
    )

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", "class"]


def test_an_inactive_server_is_refused(
    session: Session, me: TestClient, server: GameServer
) -> None:
    server.is_active = False
    session.flush()

    response = me.post("/characters", json={"name": "Maëlis", "server_id": server.id})

    assert response.status_code == 422


def test_only_admins_create_npcs(me: TestClient, admin: TestClient) -> None:
    npc = {"name": "Gardien", "is_npc": True}

    assert me.post("/characters", json=npc).status_code == 403
    created = admin.post("/characters", json=npc)
    assert created.status_code == 201
    assert created.json()["server"] is None


# Modifier


def test_the_owner_changes_only_what_is_sent(me: TestClient, mine: int) -> None:
    me.patch(f"/characters/{mine}", json={"hook": "Assieds-toi.", "level": 10})

    response = me.patch(f"/characters/{mine}", json={"level": 11})

    assert response.status_code == 200
    assert response.json()["hook"] == "Assieds-toi."
    assert response.json()["level"] == 11


def test_null_empties_an_optional_field(me: TestClient, mine: int) -> None:
    me.patch(
        f"/characters/{mine}",
        json={"hook": "Assieds-toi.", "gender": "feminine", "play_days": [6]},
    )

    body = me.patch(
        f"/characters/{mine}", json={"hook": None, "gender": None, "play_days": None}
    ).json()

    assert body["hook"] is None
    assert body["gender"] == "neutral"
    assert body["play_days"] == []


@pytest.mark.parametrize(
    "changes", [{"name": None}, {"server_id": 2}, {"class": "Crâ"}, {"level": -3}]
)
def test_invalid_changes_are_refused(me: TestClient, mine: int, changes: dict) -> None:
    assert me.patch(f"/characters/{mine}", json=changes).status_code == 422


def test_someone_else_cannot_change_my_character(
    stranger: TestClient, admin: TestClient, mine: int
) -> None:
    assert stranger.patch(f"/characters/{mine}", json={"level": 1}).status_code == 403
    assert admin.patch(f"/characters/{mine}", json={"level": 1}).status_code == 403


def test_changing_needs_a_session(
    client: TestClient, me: TestClient, mine: int
) -> None:
    me.delete("/session")

    assert client.patch(f"/characters/{mine}", json={"level": 1}).status_code == 401


def test_going_into_retreat_and_coming_back(me: TestClient, mine: int) -> None:
    away = me.patch(
        f"/characters/{mine}",
        json={
            "inactive": True,
            "inactive_note": "Parti en mer pour quelques semaines.",
        },
    ).json()
    back = me.patch(f"/characters/{mine}", json={"inactive": False}).json()

    assert away["inactive"] is True
    assert away["inactive_note"] == "Parti en mer pour quelques semaines."
    assert back["inactive"] is False
    assert back["inactive_note"] is None


# Supprimer


def test_the_owner_deletes_a_character(me: TestClient, mine: int) -> None:
    assert me.delete(f"/characters/{mine}").status_code == 204
    assert me.get(f"/characters/{mine}").status_code == 404


def test_someone_else_cannot_delete_it_but_an_admin_can(
    stranger: TestClient, admin: TestClient, mine: int
) -> None:
    assert stranger.delete(f"/characters/{mine}").status_code == 403
    assert admin.delete(f"/characters/{mine}").status_code == 204


# Lire


def test_my_characters_include_the_hidden_and_inactive_ones(
    session: Session, me: TestClient, mine: int, server: GameServer
) -> None:
    other = me.post(
        "/characters", json={"name": "Tobias", "server_id": server.id}
    ).json()
    me.patch(f"/characters/{other['id']}", json={"inactive": True})
    session.get(Character, mine).hidden_at = datetime.now(UTC)
    session.flush()

    items = me.get("/me/characters").json()["items"]

    assert {c["name"]: (c["hidden"], c["inactive"]) for c in items} == {
        "Maëlis": (True, False),
        "Tobias": (False, True),
    }
    assert all(c["is_mine"] for c in items)


def test_a_hidden_sheet_stays_readable_by_its_owner_only(
    session: Session, me: TestClient, stranger: TestClient, mine: int
) -> None:
    session.get(Character, mine).hidden_at = datetime.now(UTC)
    session.flush()

    assert me.get(f"/characters/{mine}").json()["hidden"] is True
    assert stranger.get(f"/characters/{mine}").status_code == 404


def test_moderators_see_hidden_sheets_without_owning_them(
    session: Session, admin: TestClient, mine: int
) -> None:
    session.get(Character, mine).hidden_at = datetime.now(UTC)
    session.flush()

    body = admin.get(f"/characters/{mine}").json()

    assert body["hidden"] is True
    assert body["is_mine"] is False


def test_visitors_never_see_ownership_details(
    client: TestClient, me: TestClient, mine: int
) -> None:
    me.delete("/session")

    body = client.get(f"/characters/{mine}").json()

    assert "is_mine" not in body
    assert "hidden" not in body
