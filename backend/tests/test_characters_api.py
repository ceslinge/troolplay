from datetime import UTC, datetime

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.accounts.models import User
from backend.characters.models import Character, CharacterHangout
from backend.servers.models import GameServer


def add_character(session: Session, user: User, server: GameServer, **fields) -> int:
    character = Character(user_id=user.id, server_id=server.id, name="Maëlis", **fields)
    session.add(character)
    session.flush()
    return character.id


def test_a_character_is_read_with_its_server_and_hangouts(
    session: Session, client: TestClient, user: User, server: GameServer
) -> None:
    character_id = add_character(session, user, server, class_="cra", level=142)
    session.add(CharacterHangout(character_id=character_id, area="Astrub", x=5, y=-18))
    session.flush()

    response = client.get(f"/characters/{character_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Maëlis"
    assert body["class"] == "cra"
    assert body["server"]["name"] == "Serveur de test"
    assert body["hangouts"][0]["area"] == "Astrub"
    assert body["inactive"] is False


def test_the_owner_is_never_revealed(
    session: Session, client: TestClient, user: User, server: GameServer
) -> None:
    character_id = add_character(session, user, server)

    response = client.get(f"/characters/{character_id}")

    assert "user_id" not in response.text
    assert user.email not in response.text


def test_an_inactive_character_can_still_be_read(
    session: Session, client: TestClient, user: User, server: GameServer
) -> None:
    character_id = add_character(session, user, server, inactive_at=datetime.now(UTC))

    response = client.get(f"/characters/{character_id}")

    assert response.status_code == 200
    assert response.json()["inactive"] is True


def test_a_hidden_character_is_not_found(
    session: Session, client: TestClient, user: User, server: GameServer
) -> None:
    character_id = add_character(session, user, server, hidden_at=datetime.now(UTC))

    response = client.get(f"/characters/{character_id}")

    assert response.status_code == 404


def test_an_unknown_character_is_not_found(client: TestClient) -> None:
    response = client.get("/characters/999999999")

    assert response.status_code == 404
