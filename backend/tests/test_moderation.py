from collections.abc import Iterator
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.accounts.models import User, UserSession
from backend.characters.models import Character
from backend.main import app
from backend.moderation.models import ModerationAction, Report
from backend.stories.models import Story

TEXT = "Le vent tournait. *Encore une nuit sans sommeil*, pensa-t-elle."
WHY = {"reason": "Vise un joueur précis, contraire à la charte."}


@pytest.fixture
def moderator(client: TestClient, make_member, log_in_as) -> Iterator[TestClient]:
    with TestClient(app) as other:
        yield log_in_as(other, make_member("modo.test@example.com", role="moderator"))


@pytest.fixture
def story(me: TestClient, mine: int) -> int:
    created = me.post(
        "/stories", json={"character_id": mine, "title": "La nuit", "body": TEXT}
    ).json()
    me.post(f"/stories/{created['id']}/publish")
    return created["id"]


@pytest.fixture
def reported(stranger: TestClient, story: int) -> int:
    """L'histoire du propriétaire, signalée par un autre membre."""
    stranger.post(
        "/reports",
        json={"target": "story", "target_id": story, "reason": "disrespect"},
    )
    return story


def journal(session: Session) -> list[ModerationAction]:
    return list(session.scalars(select(ModerationAction).order_by(ModerationAction.id)))


# Qui y a accès


def test_the_team_tools_are_for_moderators(
    client: TestClient, me: TestClient, moderator: TestClient
) -> None:
    assert me.get("/moderation/cases").status_code == 403
    assert moderator.get("/moderation/cases").status_code == 200
    me.delete("/session")
    assert client.get("/moderation/cases").status_code == 401


# Les dossiers


def test_reports_of_one_content_make_one_case(
    reported: int, make_member, log_in_as, moderator: TestClient
) -> None:
    with TestClient(app) as third:
        log_in_as(third, make_member("troisieme.test@example.com"))
        third.post(
            "/reports",
            json={"target": "story", "target_id": reported, "reason": "hate"},
        )

    (case,) = moderator.get("/moderation/cases").json()["items"]

    assert (case["target"], case["target_id"], case["label"]) == (
        "story",
        reported,
        "La nuit",
    )
    assert case["open_reports"] == 2
    assert case["reasons"] == {"disrespect": 1, "hate": 1}


def test_a_case_shows_the_owner_account_without_any_email(
    owner: User, reported: int, moderator: TestClient
) -> None:
    case = moderator.get(f"/moderation/cases/story/{reported}").json()

    assert case["owner"]["id"] == owner.id
    assert [c["name"] for c in case["owner"]["characters"]] == ["Maëlis"]
    assert case["reports"][0]["snapshot"]["body"] == TEXT
    assert case["reports"][0]["reporter"]["reports_sent"] == 1
    assert "@" not in str(case)


def test_deciding_closes_the_case_and_erases_the_copies(
    session: Session, reported: int, moderator: TestClient
) -> None:
    response = moderator.post(
        f"/moderation/cases/story/{reported}/decide",
        json={"decision": "founded", **WHY},
    )

    assert response.status_code == 200
    report = session.scalars(select(Report)).one()
    assert report.decision == "founded"
    assert report.snapshot is None
    assert moderator.get("/moderation/cases").json()["total"] == 0
    assert moderator.get("/moderation/cases?status=closed").json()["total"] == 1
    assert journal(session)[-1].action == "decide"
    again = moderator.post(
        f"/moderation/cases/story/{reported}/decide",
        json={"decision": "founded", **WHY},
    )
    assert again.status_code == 409


def test_a_decision_needs_a_reason(reported: int, moderator: TestClient) -> None:
    response = moderator.post(
        f"/moderation/cases/story/{reported}/decide", json={"decision": "founded"}
    )

    assert response.status_code == 422


def test_abusive_reports_show_on_their_author(
    session: Session, stranger: TestClient, reported: int, moderator: TestClient
) -> None:
    moderator.post(
        f"/moderation/cases/story/{reported}/decide",
        json={"decision": "abusive", **WHY},
    )

    reporter = moderator.get(f"/moderation/cases/story/{reported}").json()["reports"][
        0
    ]["reporter"]

    assert reporter["abusive"] == 1


# Masquer, rétablir


def test_hiding_a_story_tells_its_author_and_hides_it_from_others(
    session: Session,
    me: TestClient,
    stranger: TestClient,
    moderator: TestClient,
    story: int,
    outbox: list[dict[str, str]],
) -> None:
    response = moderator.post(f"/moderation/stories/{story}/hide", json=WHY)

    assert response.status_code == 200
    assert stranger.get(f"/stories/{story}").status_code == 404
    assert me.get(f"/stories/{story}").json()["hidden"] is True
    (mail,) = outbox
    assert mail["to"] == "proprietaire.test@example.com"
    assert WHY["reason"] in mail["body"]
    assert journal(session)[-1].action == "hide"

    moderator.post(f"/moderation/stories/{story}/unhide", json=WHY)
    assert stranger.get(f"/stories/{story}").status_code == 200


def test_hiding_twice_says_so(moderator: TestClient, mine: int) -> None:
    moderator.post(f"/moderation/characters/{mine}/hide", json=WHY)

    assert (
        moderator.post(f"/moderation/characters/{mine}/hide", json=WHY).status_code
        == 409
    )


def test_one_acts_only_on_a_lower_rank(
    session: Session,
    moderator: TestClient,
    admin: TestClient,
    server,
    make_member,
) -> None:
    other_moderator = make_member("autre.modo@example.com", role="moderator")
    theirs = Character(user_id=other_moderator.id, server_id=server.id, name="Gardien")
    npc = Character(is_npc=True, name="Le Tavernier")
    session.add_all([theirs, npc])
    session.flush()

    assert (
        moderator.post(f"/moderation/characters/{theirs.id}/hide", json=WHY).status_code
        == 403
    )
    assert (
        moderator.post(f"/moderation/characters/{npc.id}/hide", json=WHY).status_code
        == 403
    )
    assert (
        admin.post(f"/moderation/characters/{theirs.id}/hide", json=WHY).status_code
        == 200
    )
    assert (
        admin.post(f"/moderation/characters/{npc.id}/hide", json=WHY).status_code == 200
    )


# Suspendre


def test_a_suspension_ends_the_sessions_and_blocks_login(
    session: Session,
    me: TestClient,
    owner: User,
    member_password: str,
    moderator: TestClient,
    outbox: list[dict[str, str]],
) -> None:
    response = moderator.post(
        f"/moderation/accounts/{owner.id}/suspend", json={"duration": "week", **WHY}
    )

    assert response.status_code == 200
    assert response.json()["suspended"] is True
    assert me.get("/me").status_code == 401
    assert (
        session.scalars(
            select(UserSession).where(UserSession.user_id == owner.id)
        ).first()
        is None
    )
    login = me.post(
        "/session", json={"email": owner.email, "password": member_password}
    )
    assert login.status_code == 403
    assert "jusqu'au" in login.json()["detail"]
    assert "suspendu" in outbox[-1]["subject"]
    assert journal(session)[-1].detail == "week"


def test_a_suspension_lifts_itself_at_its_end(
    session: Session, client: TestClient, owner: User, log_in_as
) -> None:
    owner.banned_at = datetime.now(UTC) - timedelta(days=8)
    owner.banned_until = datetime.now(UTC) - timedelta(days=1)
    session.flush()

    log_in_as(client, owner)

    assert client.get("/me").status_code == 200


def test_forever_means_no_end(owner: User, moderator: TestClient) -> None:
    body = moderator.post(
        f"/moderation/accounts/{owner.id}/suspend", json={"duration": "forever", **WHY}
    ).json()

    assert body["suspended"] is True
    assert body["banned_until"] is None


def test_reinstating_lets_them_back_in(
    client: TestClient, owner: User, moderator: TestClient, log_in_as
) -> None:
    moderator.post(
        f"/moderation/accounts/{owner.id}/suspend", json={"duration": "month", **WHY}
    )

    response = moderator.post(f"/moderation/accounts/{owner.id}/reinstate", json=WHY)

    assert response.json()["suspended"] is False
    log_in_as(client, owner)
    assert client.get("/me").status_code == 200


def test_a_moderator_cannot_suspend_a_peer_or_an_admin(
    moderator: TestClient, make_member
) -> None:
    for role in ("moderator", "admin"):
        target = make_member(f"{role}.cible@example.com", role=role)
        response = moderator.post(
            f"/moderation/accounts/{target.id}/suspend", json={"duration": "day", **WHY}
        )
        assert response.status_code == 403


# Le droit de signaler


def test_revoking_reporting_blocks_the_button_only(
    session: Session,
    stranger: TestClient,
    moderator: TestClient,
    mine: int,
    outbox: list[dict[str, str]],
) -> None:
    reporter = session.scalars(
        select(User).where(User.email == "voisin.test@example.com")
    ).one()

    moderator.post(
        f"/moderation/accounts/{reporter.id}/reporting", json={"allowed": False, **WHY}
    )

    payload = {"target": "character", "target_id": mine, "reason": "spam"}
    refused = stranger.post("/reports", json=payload)
    assert refused.status_code == 403
    assert "mentions légales" in refused.json()["detail"]
    assert stranger.get("/me").status_code == 200
    assert "signaler" in outbox[-1]["subject"]

    moderator.post(
        f"/moderation/accounts/{reporter.id}/reporting", json={"allowed": True, **WHY}
    )
    assert stranger.post("/reports", json=payload).status_code == 202


# Le journal


def test_the_journal_lists_actions_newest_first_and_filters(
    owner: User, moderator: TestClient, mine: int, story: int
) -> None:
    moderator.post(f"/moderation/characters/{mine}/hide", json=WHY)
    moderator.post(
        f"/moderation/accounts/{owner.id}/suspend", json={"duration": "day", **WHY}
    )

    entries = moderator.get("/moderation/journal").json()["items"]
    assert [e["action"] for e in entries] == ["suspend", "hide"]
    assert all(e["reason"] == WHY["reason"] for e in entries)
    only = moderator.get("/moderation/journal?action=hide").json()
    assert only["total"] == 1


def test_the_journal_cannot_be_changed_from_the_site(moderator: TestClient) -> None:
    assert moderator.delete("/moderation/journal").status_code == 405
    assert moderator.put("/moderation/journal", json={}).status_code == 405


def test_a_story_hidden_by_the_team_stays_editable_by_its_author(
    session: Session, me: TestClient, moderator: TestClient, story: int
) -> None:
    moderator.post(f"/moderation/stories/{story}/hide", json=WHY)

    response = me.patch(f"/stories/{story}", json={"title": "La nuit, revue"})

    assert response.status_code == 200
    assert session.get(Story, story).hidden_at is not None
