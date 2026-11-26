"""Les aperçus de liens (#53) : ce qu'un visiteur voit déjà, rien de plus."""

import re
from datetime import UTC, datetime

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.characters.models import Character
from backend.servers.models import GameServer
from backend.stories.models import Story

TEXT = "Le vent tournait. Encore une nuit sans sommeil, pensa-t-elle."


def meta(html: str, name: str) -> str | None:
    found = re.search(rf'property="{re.escape(name)}" content="([^"]*)"', html)
    return found.group(1) if found else None


def preview(client: TestClient, path: str) -> str:
    response = client.get(f"/preview{path}")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    return response.text


def test_a_sheet_shows_its_name_its_line_and_where_to_find_it(
    session: Session, client: TestClient, mine: int, server: GameServer
) -> None:
    character = session.get(Character, mine)
    character.hook, character.class_, character.level = (
        "Le large ne pose pas de questions.",
        "cra",
        120,
    )
    session.flush()

    html = preview(client, f"/personnages/{mine}")

    assert meta(html, "og:title") == "Maëlis"
    assert meta(html, "og:description") == (
        f"« Le large ne pose pas de questions. » — {server.name} · Crâ niv. 120"
    )
    assert meta(html, "og:image").endswith("/apercu.png")
    assert meta(html, "og:url").endswith(f"/personnages/{mine}")


def test_what_a_member_writes_cannot_break_the_page(
    session: Session, client: TestClient, mine: int
) -> None:
    session.get(Character, mine).hook = '"><script>alert(1)</script>'
    session.flush()

    html = preview(client, f"/personnages/{mine}")

    assert "<script>" not in html
    assert "&lt;script&gt;" in html


def test_a_hidden_or_unknown_sheet_gives_only_the_site(
    session: Session, client: TestClient, mine: int
) -> None:
    session.get(Character, mine).hidden_at = datetime.now(UTC)
    session.flush()

    for path in (f"/personnages/{mine}", "/personnages/999999"):
        html = preview(client, path)
        assert meta(html, "og:title") == "tRoolPlay"
        assert "Maëlis" not in html


def test_a_story_shows_who_signs_it_never_its_title_or_text(
    me: TestClient, client: TestClient, mine: int
) -> None:
    story = me.post(
        "/stories", json={"character_id": mine, "title": "La nuit", "body": TEXT}
    ).json()
    me.post(f"/stories/{story['id']}/publish")
    client.delete("/session")

    html = preview(client, f"/histoires/{story['id']}")

    assert meta(html, "og:title") == "Une histoire de Maëlis"
    assert "La nuit" not in html
    assert "vent" not in html


def test_a_draft_or_hidden_story_gives_only_the_site(
    session: Session, me: TestClient, client: TestClient, mine: int
) -> None:
    draft = me.post(
        "/stories", json={"character_id": mine, "title": "Brouillon", "body": TEXT}
    ).json()
    hidden = me.post(
        "/stories", json={"character_id": mine, "title": "Masquée", "body": TEXT}
    ).json()
    me.post(f"/stories/{hidden['id']}/publish")
    session.get(Story, hidden["id"]).hidden_at = datetime.now(UTC)
    session.flush()

    for story in (draft, hidden):
        assert (
            meta(preview(client, f"/histoires/{story['id']}"), "og:title")
            == "tRoolPlay"
        )
