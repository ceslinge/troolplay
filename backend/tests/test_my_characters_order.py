from fastapi.testclient import TestClient

from backend.characters.routes import MAX_CHARACTERS
from backend.servers.models import GameServer


def create(client: TestClient, server: GameServer, name: str) -> int:
    response = client.post("/characters", json={"name": name, "server_id": server.id})
    assert response.status_code == 201
    return response.json()["id"]


def my_names(client: TestClient) -> list[str]:
    return [c["name"] for c in client.get("/me/characters").json()["items"]]


def test_new_characters_go_to_the_end(me: TestClient, server: GameServer) -> None:
    for name in ["Zéphyr", "Aldegonde", "Maëlis"]:
        create(me, server, name)

    assert my_names(me) == ["Zéphyr", "Aldegonde", "Maëlis"]


def test_the_owner_chooses_the_order(me: TestClient, server: GameServer) -> None:
    zephyr, aldegonde, maelis = (
        create(me, server, name) for name in ["Zéphyr", "Aldegonde", "Maëlis"]
    )

    response = me.put("/me/characters/order", json={"ids": [maelis, zephyr, aldegonde]})

    assert response.status_code == 200
    assert [c["name"] for c in response.json()["items"]] == [
        "Maëlis",
        "Zéphyr",
        "Aldegonde",
    ]
    assert my_names(me) == ["Maëlis", "Zéphyr", "Aldegonde"]


def test_a_new_character_after_reordering_still_goes_to_the_end(
    me: TestClient, server: GameServer
) -> None:
    first, second = create(me, server, "Zéphyr"), create(me, server, "Aldegonde")
    me.put("/me/characters/order", json={"ids": [second, first]})

    create(me, server, "Maëlis")

    assert my_names(me) == ["Aldegonde", "Zéphyr", "Maëlis"]


def test_the_order_must_list_every_character_once(
    me: TestClient, stranger: TestClient, server: GameServer
) -> None:
    first, second = create(me, server, "Zéphyr"), create(me, server, "Aldegonde")
    theirs = create(stranger, server, "Bruyère")

    for ids in [[first], [first, second, second], [first, second, theirs], []]:
        response = me.put("/me/characters/order", json={"ids": ids})
        assert response.status_code == 422, ids

    assert my_names(me) == ["Zéphyr", "Aldegonde"]


def test_ordering_needs_a_session(client: TestClient) -> None:
    assert client.put("/me/characters/order", json={"ids": []}).status_code == 401


def test_an_account_has_a_limited_number_of_characters(
    me: TestClient, server: GameServer
) -> None:
    for number in range(MAX_CHARACTERS):
        create(me, server, f"Personnage {number}")

    response = me.post(
        "/characters", json={"name": "Un de trop", "server_id": server.id}
    )

    assert response.status_code == 409
    assert len(my_names(me)) == MAX_CHARACTERS


def test_the_limit_is_per_account(
    me: TestClient, stranger: TestClient, server: GameServer
) -> None:
    for number in range(MAX_CHARACTERS):
        create(me, server, f"Personnage {number}")

    create(stranger, server, "Bruyère")


def test_characters_in_retreat_come_last_in_their_own_order(
    me: TestClient, server: GameServer
) -> None:
    ids = [
        create(me, server, name)
        for name in ["Aldegonde", "Bruyère", "Cendre", "Dorian"]
    ]
    me.patch(f"/characters/{ids[0]}", json={"inactive": True})
    me.patch(f"/characters/{ids[2]}", json={"inactive": True})

    assert my_names(me) == ["Bruyère", "Dorian", "Aldegonde", "Cendre"]

    me.patch(f"/characters/{ids[0]}", json={"inactive": False})

    assert my_names(me) == ["Aldegonde", "Bruyère", "Dorian", "Cendre"]
