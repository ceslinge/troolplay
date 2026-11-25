"""La documentation interactive de l'API reste éteinte, sauf en local avec API_DOCS (#56)."""

from fastapi.testclient import TestClient


def test_no_api_map_by_default(client: TestClient) -> None:
    assert client.get("/docs").status_code == 404
    assert client.get("/openapi.json").status_code == 404
    assert client.get("/redoc").status_code == 404
