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
