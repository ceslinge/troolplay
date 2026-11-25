"""Deux fiches, un même nom (#122) : on prévient, on ne bloque pas, l'équipe tranche."""

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.characters.models import Character
from backend.moderation.models import Report
from backend.servers.models import GameServer


def create(client: TestClient, server: GameServer, **fields) -> dict:
    response = client.post("/characters", json={"server_id": server.id, **fields})
    assert response.status_code == 201
    return response.json()


def check(client: TestClient, server: GameServer, **params) -> dict:
    return client.get(
        "/characters/namesakes", params={"server_id": server.id, **params}
    ).json()


def automatic(session: Session, character: int) -> list[Report]:
    return list(
        session.scalars(
            select(Report).where(
                Report.automatic.is_(True), Report.target_character_id == character
            )
        )
    )


def test_names_are_compared_without_case_or_accents(
    me: TestClient, stranger: TestClient, server: GameServer
) -> None:
    create(me, server, name="Maëlis", ingame_name="Maëlis-Sombrefeu")

    found = check(stranger, server, name="MAELIS", ingame_name="maelis-sombrefeu")

    assert found == {"name": True, "ingame_name": True}


def test_another_server_another_world(
    session: Session, me: TestClient, stranger: TestClient, server: GameServer
) -> None:
    create(me, server, name="Maëlis", ingame_name="Maelis-Sombrefeu")
    other = GameServer(game="dofus", name="Autre serveur")
    session.add(other)
    session.flush()

    assert check(stranger, other, name="Maëlis", ingame_name="Maelis-Sombrefeu") == {
        "name": False,
        "ingame_name": False,
    }


def test_ones_own_sheet_is_not_a_namesake(me: TestClient, server: GameServer) -> None:
    mine = create(me, server, name="Maëlis", ingame_name="Maelis-Sombrefeu")

    found = check(
        me, server, name="Maëlis", ingame_name="Maelis-Sombrefeu", but=mine["id"]
    )

    assert found == {"name": False, "ingame_name": False}


def test_visitors_filling_a_sheet_are_warned_too(
    client: TestClient, me: TestClient, server: GameServer
) -> None:
    create(me, server, name="Maëlis")
    client.delete("/session")

    assert check(client, server, name="Maëlis")["name"] is True


def test_a_shared_rp_name_is_only_news(
    session: Session, me: TestClient, stranger: TestClient, server: GameServer
) -> None:
    create(me, server, name="Maëlis")

    theirs = create(stranger, server, name="Maëlis")

    assert automatic(session, theirs["id"]) == []


def test_a_twin_ingame_name_is_saved_and_handed_to_the_team(
    session: Session,
    me: TestClient,
    stranger: TestClient,
    moderator: TestClient,
    server: GameServer,
    outbox: list[dict[str, str]],
) -> None:
    first = create(me, server, name="Maëlis", ingame_name="Maelis-Sombrefeu")

    second = create(stranger, server, name="Sombre", ingame_name="maëlis-sombrefeu")

    reports = automatic(session, second["id"])
    assert len(reports) == 1
    assert reports[0].reporter_id is None
    assert reports[0].reason == "impersonation"
    assert f"n°{first['id']}" in reports[0].details
    case = moderator.get(f"/moderation/cases/character/{second['id']}").json()
    assert case["reports"][0]["automatic"] is True
    # Personne d'autre n'en sait rien : ni mail, ni trace dans ce que voient les joueurs.
    assert outbox == []
    assert "Maëlis" not in str(second)
    assert "first" not in second and "twin" not in second


def test_editing_into_a_twin_name_opens_one_case_only(
    session: Session, me: TestClient, stranger: TestClient, server: GameServer
) -> None:
    create(me, server, name="Maëlis", ingame_name="Maelis-Sombrefeu")
    theirs = create(stranger, server, name="Sombre")

    for _ in range(2):
        stranger.patch(
            f"/characters/{theirs['id']}", json={"ingame_name": "Maelis-Sombrefeu"}
        )

    assert len(automatic(session, theirs["id"])) == 1


def test_an_npc_has_no_ingame_twin(
    session: Session, me: TestClient, stranger: TestClient, server: GameServer
) -> None:
    session.add(
        Character(
            user_id=None,
            server_id=None,
            is_npc=True,
            name="Gardien",
            ingame_name="Gardien",
        )
    )
    session.flush()

    assert check(stranger, server, ingame_name="Gardien")["ingame_name"] is False
