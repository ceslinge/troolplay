import pytest
from fastapi.testclient import TestClient


def place(area: str = "Astrub", x: int = 5, y: int = -18, **more: object) -> dict:
    return {"area": area, "x": x, "y": y} | more


def put(client: TestClient, character_id: int, hangouts: list[dict]):
    return client.put(f"/characters/{character_id}/hangouts", json=hangouts)


def test_the_list_is_saved_and_shown_on_the_sheet(me: TestClient, mine: int) -> None:
    response = put(
        me,
        mine,
        [
            place(label="Taverne du Bouftou Ivre", habits="Accoudée au comptoir."),
            place("Bonta", -28, -56),
        ],
    )

    assert response.status_code == 200
    saved = response.json()
    assert [h["area"] for h in saved] == ["Astrub", "Bonta"]
    assert all("id" in h for h in saved)
    sheet = me.get(f"/characters/{mine}").json()
    assert [h["label"] for h in sheet["hangouts"]] == ["Taverne du Bouftou Ivre", None]


def test_a_new_list_replaces_the_old_one(me: TestClient, mine: int) -> None:
    put(me, mine, [place(), place("Bonta", -28, -56)])

    put(me, mine, [place("Madrestam", 7, -4)])

    assert [h["area"] for h in me.get(f"/characters/{mine}").json()["hangouts"]] == [
        "Madrestam"
    ]


def test_an_empty_list_removes_every_place(me: TestClient, mine: int) -> None:
    put(me, mine, [place()])

    assert put(me, mine, []).json() == []
    assert me.get(f"/characters/{mine}").json()["hangouts"] == []


def test_more_than_three_places_is_a_conflict(me: TestClient, mine: int) -> None:
    four = [place(x=i) for i in range(4)]

    assert put(me, mine, four).status_code == 409


def test_the_same_place_twice_is_refused(me: TestClient, mine: int) -> None:
    response = put(me, mine, [place(), place(area="astrub ")])

    assert response.status_code == 422


@pytest.mark.parametrize(
    "bad",
    [
        {"x": 5, "y": -18},
        place(area=""),
        place(x=5000),
        place(label="x" * 61),
        place(habits="x" * 201),
        place(character_id=1),
    ],
)
def test_invalid_places_are_refused(me: TestClient, mine: int, bad: dict) -> None:
    assert put(me, mine, [bad]).status_code == 422


def test_only_the_owner_sets_the_places(
    client: TestClient, me: TestClient, stranger: TestClient, mine: int
) -> None:
    assert put(stranger, mine, [place()]).status_code == 403
    me.delete("/session")
    assert put(client, mine, [place()]).status_code == 401


def test_an_unknown_character_is_not_found(me: TestClient) -> None:
    assert put(me, 999999999, [place()]).status_code == 404
