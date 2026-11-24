from collections.abc import Iterator
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.characters.models import Character
from backend.main import app
from backend.servers.models import GameServer
from backend.stories.models import Story
from backend.stories.routes import CREATE_LIMIT, MAX_DRAFTS, PUBLISH_LIMIT

TEXT = "Le vent tournait. *Encore une nuit sans sommeil*, pensa-t-elle."


@pytest.fixture
def draft(me: TestClient, mine: int) -> int:
    response = me.post(
        "/stories", json={"character_id": mine, "title": "La nuit", "body": TEXT}
    )
    assert response.status_code == 201
    return response.json()["id"]


@pytest.fixture
def published(me: TestClient, draft: int) -> int:
    assert me.post(f"/stories/{draft}/publish").status_code == 200
    return draft


@pytest.fixture
def moderator(client: TestClient, make_member, log_in_as) -> Iterator[TestClient]:
    with TestClient(app) as other:
        yield log_in_as(other, make_member("modo.test@example.com", role="moderator"))


# Écrire


def test_a_story_is_born_a_draft_signed_by_my_character(
    me: TestClient, mine: int
) -> None:
    response = me.post("/stories", json={"character_id": mine, "title": "La nuit"})

    assert response.status_code == 201
    body = response.json()
    assert body["published"] is False
    assert body["published_at"] is None
    assert body["character"]["name"] == "Maëlis"
    assert body["is_mine"] is True
    assert body["hidden"] is False
    assert body["body"] == ""


def test_i_sign_only_with_my_own_characters(
    me: TestClient, stranger: TestClient, mine: int
) -> None:
    response = stranger.post("/stories", json={"character_id": mine, "title": "Vol"})

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", "character_id"]


def test_a_character_in_retreat_can_still_sign(me: TestClient, mine: int) -> None:
    me.patch(f"/characters/{mine}", json={"inactive": True})

    response = me.post("/stories", json={"character_id": mine, "title": "Souvenirs"})

    assert response.status_code == 201


@pytest.mark.parametrize(
    "fields",
    [
        {"title": ""},
        {"title": "x" * 121},
        {"body": "x" * 50_001},
        {"content_warnings": ["gore"]},
        {"content_warnings": ["death", "death"]},
        {"content_note": "x" * 201},
    ],
)
def test_the_fields_keep_their_limits(me: TestClient, mine: int, fields: dict) -> None:
    payload = {"character_id": mine, "title": "La nuit"} | fields

    assert me.post("/stories", json=payload).status_code == 422


def test_reading_and_writing_need_a_session(client: TestClient, published: int) -> None:
    client.delete("/session")

    assert client.get(f"/stories/{published}").status_code == 401
    assert client.get("/stories?server_id=1").status_code == 401
    assert client.post("/stories", json={"title": "x"}).status_code == 401


# Brouillons et publication


def test_a_draft_exists_only_for_its_author(
    me: TestClient, stranger: TestClient, admin: TestClient, draft: int
) -> None:
    assert me.get(f"/stories/{draft}").status_code == 200
    assert stranger.get(f"/stories/{draft}").status_code == 404
    assert admin.get(f"/stories/{draft}").status_code == 404


def test_publishing_opens_it_to_members(
    me: TestClient, stranger: TestClient, draft: int
) -> None:
    response = me.post(f"/stories/{draft}/publish")

    assert response.status_code == 200
    assert response.json()["published"] is True
    other_view = stranger.get(f"/stories/{draft}").json()
    assert other_view["body"] == TEXT
    assert other_view["is_mine"] is False
    assert "hidden" not in other_view


def test_an_empty_story_cannot_be_published(me: TestClient, mine: int) -> None:
    story = me.post("/stories", json={"character_id": mine, "title": "Bientôt"})

    response = me.post(f"/stories/{story.json()['id']}/publish")

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", "body"]


def test_publishing_twice_changes_nothing(me: TestClient, published: int) -> None:
    first = me.get(f"/stories/{published}").json()["published_at"]

    response = me.post(f"/stories/{published}/publish")

    assert response.json()["published_at"] == first


def test_unpublishing_makes_it_a_draft_again(
    me: TestClient, stranger: TestClient, published: int
) -> None:
    response = me.post(f"/stories/{published}/unpublish")

    assert response.json()["published"] is False
    assert stranger.get(f"/stories/{published}").status_code == 404


def test_only_ten_publications_a_day(me: TestClient, mine: int) -> None:
    statuses = []
    for n in range(PUBLISH_LIMIT + 1):
        story = me.post(
            "/stories", json={"character_id": mine, "title": f"{n}", "body": TEXT}
        ).json()
        statuses.append(me.post(f"/stories/{story['id']}/publish").status_code)

    assert statuses == [200] * PUBLISH_LIMIT + [429]


def test_only_its_author_publishes_it(
    stranger: TestClient, admin: TestClient, published: int
) -> None:
    assert stranger.post(f"/stories/{published}/unpublish").status_code == 403
    assert admin.post(f"/stories/{published}/unpublish").status_code == 403


# Modifier


def test_a_published_story_can_be_corrected_and_stays_published(
    me: TestClient, published: int
) -> None:
    response = me.patch(f"/stories/{published}", json={"title": "La longue nuit"})

    assert response.status_code == 200
    assert response.json()["title"] == "La longue nuit"
    assert response.json()["published"] is True


def test_a_published_story_cannot_be_emptied(me: TestClient, published: int) -> None:
    assert me.patch(f"/stories/{published}", json={"body": "   "}).status_code == 422


@pytest.mark.parametrize("field", ["title", "body", "content_warnings", "character_id"])
def test_required_fields_cannot_be_erased(
    me: TestClient, draft: int, field: str
) -> None:
    assert me.patch(f"/stories/{draft}", json={field: None}).status_code == 422


def test_the_note_can_be_erased(me: TestClient, draft: int) -> None:
    me.patch(f"/stories/{draft}", json={"content_note": "Une mort"})

    response = me.patch(f"/stories/{draft}", json={"content_note": None})

    assert response.json()["content_note"] is None


def test_only_its_author_edits_it(
    stranger: TestClient, admin: TestClient, published: int
) -> None:
    assert (
        stranger.patch(f"/stories/{published}", json={"title": "x"}).status_code == 403
    )
    assert admin.patch(f"/stories/{published}", json={"title": "x"}).status_code == 403


def test_it_can_be_signed_by_another_of_my_characters(
    me: TestClient, draft: int, server: GameServer
) -> None:
    other = me.post("/characters", json={"name": "Tobias", "server_id": server.id})

    response = me.patch(f"/stories/{draft}", json={"character_id": other.json()["id"]})

    assert response.json()["character"]["name"] == "Tobias"


# Lister


def test_the_community_lists_published_stories_of_the_server_newest_first(
    me: TestClient, stranger: TestClient, mine: int, server: GameServer
) -> None:
    ids = []
    for title in ("Première", "Seconde"):
        story = me.post(
            "/stories", json={"character_id": mine, "title": title, "body": TEXT}
        ).json()
        me.post(f"/stories/{story['id']}/publish")
        ids.append(story["id"])
    me.post("/stories", json={"character_id": mine, "title": "Brouillon"})

    body = stranger.get(f"/stories?server_id={server.id}").json()

    assert [s["title"] for s in body["items"]] == ["Seconde", "Première"]
    assert body["total"] == 2
    assert body["items"][0]["excerpt"] == TEXT.replace("*", "")
    assert "body" not in body["items"][0]


def test_a_character_page_lists_its_stories(
    stranger: TestClient, mine: int, published: int
) -> None:
    body = stranger.get(f"/stories?character_id={mine}").json()

    assert [s["id"] for s in body["items"]] == [published]


def test_listing_needs_a_server_or_a_character(me: TestClient, server) -> None:
    assert me.get("/stories").status_code == 422
    assert me.get(f"/stories?server_id={server.id}&character_id=1").status_code == 422


def test_a_warned_story_shows_no_excerpt(
    me: TestClient, mine: int, server: GameServer
) -> None:
    story = me.post(
        "/stories",
        json={
            "character_id": mine,
            "title": "Le deuil",
            "body": TEXT,
            "content_warnings": ["death"],
            "content_note": "Mort d'un personnage aimé",
        },
    ).json()
    me.post(f"/stories/{story['id']}/publish")

    item = me.get(f"/stories?server_id={server.id}").json()["items"][0]

    assert item["excerpt"] is None
    assert item["content_warnings"] == ["death"]
    assert item["content_note"] == "Mort d'un personnage aimé"


def test_a_long_excerpt_stops_at_a_word(
    me: TestClient, mine: int, server: GameServer
) -> None:
    long_text = "Le vent tournait encore " * 30
    story = me.post(
        "/stories", json={"character_id": mine, "title": "Long", "body": long_text}
    ).json()
    me.post(f"/stories/{story['id']}/publish")

    excerpt = me.get(f"/stories?server_id={server.id}").json()["items"][0]["excerpt"]

    assert len(excerpt) <= 201
    assert excerpt.endswith("…")
    assert long_text.startswith(excerpt[:-1])


def test_hidden_stories_and_hidden_characters_stay_out_of_lists(
    session: Session, stranger: TestClient, mine: int, published: int, server
) -> None:
    session.get(Story, published).hidden_at = datetime.now(UTC)
    session.flush()
    assert stranger.get(f"/stories?server_id={server.id}").json()["total"] == 0

    session.get(Story, published).hidden_at = None
    session.get(Character, mine).hidden_at = datetime.now(UTC)
    session.flush()
    assert stranger.get(f"/stories?server_id={server.id}").json()["total"] == 0


def test_my_stories_include_drafts_last_edited_first(
    me: TestClient, mine: int, published: int
) -> None:
    me.post("/stories", json={"character_id": mine, "title": "Brouillon"})

    items = me.get("/me/stories").json()["items"]

    assert [(s["title"], s["published"]) for s in items] == [
        ("Brouillon", False),
        ("La nuit", True),
    ]
    assert all(s["hidden"] is False for s in items)


# Masquer, et ce que voit la modération


def test_a_hidden_story_is_read_by_its_author_and_moderators_only(
    session: Session,
    me: TestClient,
    stranger: TestClient,
    moderator: TestClient,
    published: int,
) -> None:
    session.get(Story, published).hidden_at = datetime.now(UTC)
    session.flush()

    assert me.get(f"/stories/{published}").json()["hidden"] is True
    assert stranger.get(f"/stories/{published}").status_code == 404
    seen = moderator.get(f"/stories/{published}").json()
    assert seen["hidden"] is True
    assert seen["is_mine"] is False


# Supprimer


def test_its_author_deletes_it(me: TestClient, draft: int) -> None:
    assert me.delete(f"/stories/{draft}").status_code == 204
    assert me.get(f"/stories/{draft}").status_code == 404


def test_an_admin_deletes_a_published_story_a_moderator_does_not(
    moderator: TestClient, admin: TestClient, published: int
) -> None:
    assert moderator.delete(f"/stories/{published}").status_code == 403
    assert admin.delete(f"/stories/{published}").status_code == 204


def test_a_story_outlives_its_character_without_a_signature(
    me: TestClient, mine: int, published: int, server: GameServer
) -> None:
    me.delete(f"/characters/{mine}")

    story = me.get(f"/stories/{published}").json()

    assert story["character"] is None
    assert me.get(f"/stories?server_id={server.id}").json()["total"] == 0
    assert me.post(f"/stories/{published}/unpublish").status_code == 200
    response = me.post(f"/stories/{published}/publish")
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", "character_id"]


def test_stories_leave_with_the_account(
    session: Session, me: TestClient, member_password: str, published: int
) -> None:
    response = me.request("DELETE", "/me", json={"password": member_password})

    assert response.status_code == 204
    assert session.get(Story, published) is None


# Ce qu'on ne renvoie jamais


def test_no_story_response_carries_a_user_id(
    me: TestClient, stranger: TestClient, mine: int, published: int, server
) -> None:
    responses = [
        stranger.get(f"/stories/{published}").json(),
        stranger.get(f"/stories?server_id={server.id}").json(),
        me.get("/me/stories").json(),
    ]

    assert all("user_id" not in str(r) for r in responses)


# Contre le remplissage à coups de script


def test_at_most_thirty_drafts_at_once(
    session: Session, me: TestClient, owner, mine: int
) -> None:
    for n in range(MAX_DRAFTS):
        session.add(Story(user_id=owner.id, character_id=mine, title=f"{n}"))
    session.flush()

    response = me.post("/stories", json={"character_id": mine, "title": "De trop"})

    assert response.status_code == 409
    assert "brouillons" in response.json()["detail"]


def test_unpublishing_counts_towards_the_drafts(
    session: Session, me: TestClient, owner, mine: int, published: int
) -> None:
    for n in range(MAX_DRAFTS):
        session.add(Story(user_id=owner.id, character_id=mine, title=f"{n}"))
    session.flush()

    assert me.post(f"/stories/{published}/unpublish").status_code == 409
    assert me.get(f"/stories/{published}").json()["published"] is True


def test_at_most_thirty_stories_created_an_hour(me: TestClient, mine: int) -> None:
    statuses = []
    for n in range(CREATE_LIMIT + 1):
        response = me.post("/stories", json={"character_id": mine, "title": f"{n}"})
        statuses.append(response.status_code)
        if response.status_code == 201:
            me.delete(f"/stories/{response.json()['id']}")

    assert statuses == [201] * CREATE_LIMIT + [429]


# Le mot de l'auteur


def test_the_author_note_is_kept_apart_and_can_be_erased(
    me: TestClient, stranger: TestClient, published: int
) -> None:
    note = "Suite de la soirée du 12 à la taverne. Merci à Tobias !"
    me.patch(f"/stories/{published}", json={"author_note": note})

    assert stranger.get(f"/stories/{published}").json()["author_note"] == note
    erased = me.patch(f"/stories/{published}", json={"author_note": None})
    assert erased.json()["author_note"] is None


def test_the_author_note_has_a_limit(me: TestClient, mine: int) -> None:
    payload = {"character_id": mine, "title": "La nuit", "author_note": "x" * 1001}

    assert me.post("/stories", json=payload).status_code == 422


def test_lists_give_a_reading_time(
    me: TestClient, mine: int, server: GameServer
) -> None:
    for title, words in (("Courte", 10), ("Longue", 2300)):
        story = me.post(
            "/stories",
            json={"character_id": mine, "title": title, "body": "mot " * words},
        ).json()
        me.post(f"/stories/{story['id']}/publish")

    items = me.get(f"/stories?server_id={server.id}").json()["items"]

    assert {s["title"]: s["reading_minutes"] for s in items} == {
        "Longue": 10,
        "Courte": 1,
    }


def test_an_excerpt_drops_the_formatting_marks(
    me: TestClient, mine: int, server: GameServer
) -> None:
    body = "Le vent. *Encore une nuit*, pensa-t-elle. **Un *vrai* cri.** Un astérisque * seul."
    story = me.post(
        "/stories", json={"character_id": mine, "title": "Marques", "body": body}
    ).json()
    me.post(f"/stories/{story['id']}/publish")

    excerpt = me.get(f"/stories?server_id={server.id}").json()["items"][0]["excerpt"]

    assert (
        excerpt
        == "Le vent. Encore une nuit, pensa-t-elle. Un vrai cri. Un astérisque * seul."
    )
