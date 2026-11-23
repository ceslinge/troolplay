from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.servers.models import GameServer


def test_only_active_servers_are_listed(session: Session, client: TestClient) -> None:
    session.add(GameServer(game="dofus", name="Serveur de test"))
    session.add(GameServer(game="dofus", name="Serveur fermé de test", is_active=False))
    session.flush()

    response = client.get("/servers")

    assert response.status_code == 200
    names = [server["name"] for server in response.json()["items"]]
    assert "Serveur de test" in names
    assert "Serveur fermé de test" not in names


def test_a_server_lists_the_classes_of_its_game(
    session: Session, client: TestClient
) -> None:
    session.add(GameServer(game="retro", name="Serveur rétro de test"))
    session.flush()

    response = client.get("/servers")

    retro = next(
        s for s in response.json()["items"] if s["name"] == "Serveur rétro de test"
    )
    assert len(retro["classes"]) == 12
    assert "roublard" not in retro["classes"]
