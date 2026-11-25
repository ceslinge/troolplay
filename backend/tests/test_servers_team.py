from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from support import journal

from backend.servers.models import GameServer

WHY = {"reason": "Ankama l'a annoncé ce matin."}


def test_servers_are_for_admins_only(
    me: TestClient, moderator: TestClient, server: GameServer
) -> None:
    for client in (me, moderator):
        assert client.get("/moderation/servers").status_code == 403
        assert (
            client.post(f"/moderation/servers/{server.id}/close", json=WHY).status_code
            == 403
        )


def test_the_list_shows_closed_servers_and_counts(
    admin: TestClient, server: GameServer, mine: int
) -> None:
    admin.post(f"/moderation/servers/{server.id}/close", json=WHY)

    row = next(
        s
        for s in admin.get("/moderation/servers").json()["items"]
        if s["id"] == server.id
    )

    assert row["closed"] is True
    assert row["characters"] == 1
    assert row["stories"] == 0


def test_adding_a_server_opens_it_and_writes_it_down(
    session: Session, admin: TestClient, client: TestClient
) -> None:
    response = admin.post(
        "/moderation/servers", json={"game": "dofus", "name": " Nouvelle Lune ", **WHY}
    )

    assert response.status_code == 201
    added = response.json()
    assert added["name"] == "Nouvelle Lune" and added["closed"] is False
    assert any(s["id"] == added["id"] for s in client.get("/servers").json()["items"])
    entry = journal(session)[-1]
    assert (entry.action, entry.target_server_id) == ("add_server", added["id"])


def test_a_name_is_taken_once_per_game(admin: TestClient, server: GameServer) -> None:
    same = admin.post(
        "/moderation/servers",
        json={"game": "dofus", "name": server.name.upper(), **WHY},
    )
    other_game = admin.post(
        "/moderation/servers", json={"game": "retro", "name": server.name, **WHY}
    )

    assert same.status_code == 422
    assert other_game.status_code == 201


def test_renaming_keeps_the_old_name_in_the_journal(
    session: Session, admin: TestClient, server: GameServer, mine: int, me: TestClient
) -> None:
    old = server.name

    response = admin.patch(
        f"/moderation/servers/{server.id}", json={"name": "Brial-Est", **WHY}
    )

    assert response.json()["name"] == "Brial-Est"
    assert me.get(f"/characters/{mine}").json()["server"]["name"] == "Brial-Est"
    entry = journal(session)[-1]
    assert (entry.action, entry.detail) == ("rename_server", old)


def test_closing_keeps_the_sheets_but_stops_new_ones(
    session: Session, admin: TestClient, me: TestClient, server: GameServer, mine: int
) -> None:
    assert (
        admin.post(f"/moderation/servers/{server.id}/close", json=WHY).status_code
        == 200
    )

    sheet = me.get(f"/characters/{mine}")
    assert sheet.status_code == 200
    assert sheet.json()["server"]["closed"] is True
    assert (
        me.patch(f"/characters/{mine}", json={"hook": "Toujours là."}).status_code
        == 200
    )
    created = me.post(
        "/characters",
        json={"name": "Tardif", "server_id": server.id, "gender": "neutral"},
    )
    assert created.status_code == 422
    assert all(s["id"] != server.id for s in me.get("/servers").json()["items"])
    assert journal(session)[-1].action == "close_server"


def test_reopening_and_saying_so_twice(admin: TestClient, server: GameServer) -> None:
    assert (
        admin.post(f"/moderation/servers/{server.id}/reopen", json=WHY).status_code
        == 409
    )
    admin.post(f"/moderation/servers/{server.id}/close", json=WHY)
    assert (
        admin.post(f"/moderation/servers/{server.id}/close", json=WHY).status_code
        == 409
    )

    assert (
        admin.post(f"/moderation/servers/{server.id}/reopen", json=WHY).json()["closed"]
        is False
    )


def test_every_server_gesture_needs_a_reason(
    admin: TestClient, server: GameServer
) -> None:
    assert (
        admin.post(f"/moderation/servers/{server.id}/close", json={}).status_code == 422
    )
    assert (
        admin.patch(
            f"/moderation/servers/{server.id}", json={"name": "Sans raison"}
        ).status_code
        == 422
    )


def test_the_journal_names_the_server(admin: TestClient, server: GameServer) -> None:
    admin.post(f"/moderation/servers/{server.id}/close", json=WHY)

    entry = admin.get("/moderation/journal?action=close_server").json()["items"][0]

    assert entry["target_server_id"] == server.id
    assert entry["target_server_name"] == server.name


def test_a_name_of_spaces_is_no_name(admin: TestClient, server: GameServer) -> None:
    blank = admin.post(
        "/moderation/servers", json={"game": "dofus", "name": "    ", **WHY}
    )
    renamed = admin.patch(
        f"/moderation/servers/{server.id}", json={"name": " x ", **WHY}
    )

    assert blank.status_code == 422
    assert renamed.status_code == 422
