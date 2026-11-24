from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.accounts.models import User
from backend.characters.models import Character
from backend.moderation.models import Report
from backend.moderation.routes import REPORT_LIMIT
from backend.stories.models import Story

TEXT = "Le vent tournait. *Encore une nuit sans sommeil*, pensa-t-elle."


@pytest.fixture
def story(me: TestClient, mine: int) -> int:
    created = me.post(
        "/stories", json={"character_id": mine, "title": "La nuit", "body": TEXT}
    ).json()
    me.post(f"/stories/{created['id']}/publish")
    return created["id"]


def reports(session: Session) -> list[Report]:
    return list(session.scalars(select(Report).order_by(Report.id)))


def test_a_member_reports_a_character_with_a_copy_of_it(
    session: Session, stranger: TestClient, owner: User, mine: int
) -> None:
    response = stranger.post(
        "/reports",
        json={"target": "character", "target_id": mine, "reason": "off_topic"},
    )

    assert response.status_code == 202
    assert "équipe" in response.json()["detail"]
    (report,) = reports(session)
    assert report.target_character_id == mine
    assert report.target_story_id is None
    assert report.reported_user_id == owner.id
    assert report.reason == "off_topic"
    assert report.snapshot["name"] == "Maëlis"
    assert report.handled_at is None


def test_a_member_reports_a_story_with_a_copy_of_it(
    session: Session, stranger: TestClient, story: int
) -> None:
    response = stranger.post(
        "/reports",
        json={
            "target": "story",
            "target_id": story,
            "reason": "disrespect",
            "details": "  Vise un joueur précis.  ",
        },
    )

    assert response.status_code == 202
    (report,) = reports(session)
    assert report.target_story_id == story
    assert report.details == "Vise un joueur précis."
    assert report.snapshot["body"] == TEXT
    assert "is_mine" not in report.snapshot


def test_the_copy_keeps_what_was_reported_even_if_it_changes(
    session: Session, me: TestClient, stranger: TestClient, story: int
) -> None:
    stranger.post(
        "/reports", json={"target": "story", "target_id": story, "reason": "spam"}
    )
    me.patch(f"/stories/{story}", json={"body": "Tout a été réécrit."})

    assert reports(session)[0].snapshot["body"] == TEXT


def test_nobody_reports_their_own_content(
    me: TestClient, mine: int, story: int
) -> None:
    for target, target_id in (("character", mine), ("story", story)):
        response = me.post(
            "/reports",
            json={"target": target, "target_id": target_id, "reason": "spam"},
        )
        assert response.status_code == 422


def test_one_reports_only_what_one_can_read(
    me: TestClient, stranger: TestClient, mine: int
) -> None:
    draft = me.post("/stories", json={"character_id": mine, "title": "Brouillon"})

    response = stranger.post(
        "/reports",
        json={"target": "story", "target_id": draft.json()["id"], "reason": "spam"},
    )

    assert response.status_code == 404
    assert (
        stranger.post(
            "/reports",
            json={"target": "character", "target_id": 999_999, "reason": "spam"},
        ).status_code
        == 404
    )


def test_reporting_needs_a_session(client: TestClient, mine: int) -> None:
    client.delete("/session")

    response = client.post(
        "/reports", json={"target": "character", "target_id": mine, "reason": "spam"}
    )

    assert response.status_code == 401


def test_other_needs_a_few_words(stranger: TestClient, mine: int) -> None:
    payload = {"target": "character", "target_id": mine, "reason": "other"}

    assert stranger.post("/reports", json=payload).status_code == 422
    payload["details"] = "Le nom imite celui d'un joueur."
    assert stranger.post("/reports", json=payload).status_code == 202


@pytest.mark.parametrize(
    "fields",
    [{"reason": "boring"}, {"target": "server"}, {"details": "x" * 1001}],
)
def test_the_fields_keep_their_limits(
    stranger: TestClient, mine: int, fields: dict
) -> None:
    payload = {"target": "character", "target_id": mine, "reason": "spam"} | fields

    assert stranger.post("/reports", json=payload).status_code == 422


def test_reporting_twice_counts_once(
    session: Session, stranger: TestClient, mine: int
) -> None:
    payload = {"target": "character", "target_id": mine, "reason": "spam"}

    assert stranger.post("/reports", json=payload).status_code == 202
    assert stranger.post("/reports", json=payload).status_code == 202
    assert len(reports(session)) == 1


def test_at_most_ten_reports_an_hour(
    session: Session, stranger: TestClient, make_member, server
) -> None:
    targets = []
    for n in range(REPORT_LIMIT + 1):
        author = make_member(f"auteur{n}.test@example.com")
        character = Character(user_id=author.id, server_id=server.id, name=f"Perso {n}")
        session.add(character)
        session.flush()
        targets.append(character.id)

    statuses = [
        stranger.post(
            "/reports",
            json={"target": "character", "target_id": t, "reason": "spam"},
        ).status_code
        for t in targets
    ]

    assert statuses == [202] * REPORT_LIMIT + [429]


def test_a_report_outlives_the_content_and_both_accounts(
    session: Session,
    me: TestClient,
    stranger: TestClient,
    member_password: str,
    mine: int,
    story: int,
) -> None:
    stranger.post(
        "/reports", json={"target": "story", "target_id": story, "reason": "spam"}
    )
    stranger.request("DELETE", "/me", json={"password": member_password})
    me.request("DELETE", "/me", json={"password": member_password})
    session.expire_all()

    (report,) = reports(session)
    assert report.reporter_id is None
    assert report.reported_user_id is None
    assert report.target_story_id is None
    assert report.snapshot["title"] == "La nuit"
    assert session.get(Story, story) is None


def test_hidden_content_is_reported_only_by_who_can_see_it(
    session: Session, stranger: TestClient, admin: TestClient, mine: int
) -> None:
    session.get(Character, mine).hidden_at = datetime.now(UTC)
    session.flush()
    payload = {"target": "character", "target_id": mine, "reason": "spam"}

    assert stranger.post("/reports", json=payload).status_code == 404
    assert admin.post("/reports", json=payload).status_code == 202
