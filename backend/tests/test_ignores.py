from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.characters.models import Character, CharacterHangout
from backend.servers.models import GameServer

TEXT = "Le vent tournait. Encore une nuit sans sommeil, pensa-t-elle."


def ignore(client: TestClient, character_id: int) -> int:
    return client.put(f"/me/ignored/{character_id}").status_code


def test_ignoring_takes_them_out_of_my_directory_only(
    me: TestClient, stranger: TestClient, mine: int, server: GameServer
) -> None:
    assert ignore(stranger, mine) == 204

    assert stranger.get(f"/characters?server_id={server.id}").json()["total"] == 0
    assert me.get(f"/characters?server_id={server.id}").json()["total"] == 1


def test_visitors_see_everyone(
    client: TestClient, stranger: TestClient, mine: int, server: GameServer
) -> None:
    ignore(stranger, mine)

    with TestClient(client.app) as visitor:
        assert visitor.get(f"/characters?server_id={server.id}").json()["total"] == 1


def test_ignored_characters_leave_the_places(
    session: Session, stranger: TestClient, mine: int, server: GameServer
) -> None:
    session.add(CharacterHangout(character_id=mine, area="Astrub", x=5, y=-18))
    session.flush()
    assert len(stranger.get(f"/servers/{server.id}/places").json()["items"]) == 1

    ignore(stranger, mine)

    assert stranger.get(f"/servers/{server.id}/places").json()["items"] == []


def test_their_stories_leave_the_server_list_but_not_their_sheet(
    me: TestClient, stranger: TestClient, mine: int, server: GameServer
) -> None:
    story = me.post(
        "/stories", json={"character_id": mine, "title": "La nuit", "body": TEXT}
    ).json()
    me.post(f"/stories/{story['id']}/publish")

    ignore(stranger, mine)

    assert stranger.get(f"/stories?server_id={server.id}").json()["total"] == 0
    assert stranger.get(f"/stories?character_id={mine}").json()["total"] == 1
    assert stranger.get(f"/stories/{story['id']}").status_code == 200


def test_the_home_page_leaves_them_out(
    session: Session, stranger: TestClient, mine: int
) -> None:
    session.get(Character, mine).hook = "Assieds-toi."
    session.flush()
    before = stranger.get("/home").json()
    assert any(c["id"] == mine for c in before["recent"])

    ignore(stranger, mine)

    after = stranger.get("/home").json()
    assert all(c["id"] != mine for c in after["recent"])
    assert after["overheard"] is None or after["overheard"]["character_id"] != mine
    another = stranger.get("/home/overheard").json()
    assert another is None or another["character_id"] != mine


def test_the_sheet_stays_open_and_says_so_to_me_alone(
    me: TestClient, stranger: TestClient, mine: int
) -> None:
    ignore(stranger, mine)

    assert stranger.get(f"/characters/{mine}").json()["ignored"] is True
    assert me.get(f"/characters/{mine}").json()["ignored"] is False


def test_one_does_not_ignore_oneself(me: TestClient, mine: int) -> None:
    response = me.put(f"/me/ignored/{mine}")

    assert response.status_code == 422


def test_ignoring_twice_changes_nothing_and_can_be_undone(
    stranger: TestClient, mine: int, server: GameServer
) -> None:
    assert ignore(stranger, mine) == 204
    assert ignore(stranger, mine) == 204
    assert [c["id"] for c in stranger.get("/me/ignored").json()["items"]] == [mine]

    assert stranger.delete(f"/me/ignored/{mine}").status_code == 204

    assert stranger.get("/me/ignored").json()["items"] == []
    assert stranger.get(f"/characters?server_id={server.id}").json()["total"] == 1


def test_a_hidden_or_unknown_character_cannot_be_ignored(
    stranger: TestClient,
) -> None:
    assert stranger.put("/me/ignored/999999").status_code == 404


def test_ignoring_needs_a_session(client: TestClient, mine: int) -> None:
    client.delete("/session")

    assert client.put(f"/me/ignored/{mine}").status_code == 401
    assert client.get("/me/ignored").status_code == 401


def test_nobody_learns_who_ignores_whom(
    me: TestClient, stranger: TestClient, mine: int
) -> None:
    ignore(stranger, mine)

    # Le propriétaire ne voit rien changer, sur sa fiche comme dans ses listes.
    assert me.get(f"/characters/{mine}").json()["ignored"] is False
    assert "ignored" not in me.get("/me/characters").json()["items"][0]
