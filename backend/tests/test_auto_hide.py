from collections.abc import Callable, Iterator
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.accounts.models import User
from backend.config import settings
from backend.main import app
from backend.moderation.models import ModerationAction, Report
from backend.stories.models import Story

TEXT = "Je sais où tu habites. Tu le regretteras."
WHY = {"reason": "Rien de contraire à la charte."}


@pytest.fixture
def story(me: TestClient, mine: int) -> int:
    created = me.post(
        "/stories", json={"character_id": mine, "title": "Une lettre", "body": TEXT}
    ).json()
    me.post(f"/stories/{created['id']}/publish")
    return created["id"]


@pytest.fixture
def reporter(
    session: Session, make_member, log_in_as
) -> Iterator[Callable[..., TestClient]]:
    """Fabrique un membre qui signale, fiable par défaut : vérifié, et inscrit depuis un moment."""
    clients: list[TestClient] = []

    def make(n: int, *, age_days: int = 10, verified: bool = True) -> TestClient:
        user = make_member(f"signaleur{n}.test@example.com")
        user.created_at = datetime.now(UTC) - timedelta(days=age_days)
        session.flush()
        other = TestClient(app)
        clients.append(other)
        log_in_as(other, user)
        if not verified:
            user.email_verified_at = None
            session.flush()
        return other

    yield make
    for c in clients:
        c.close()


def report(client: TestClient, story: int) -> None:
    response = client.post(
        "/reports", json={"target": "story", "target_id": story, "reason": "illegal"}
    )
    assert response.status_code == 202


def hidden(session: Session, story: int) -> bool:
    session.expire_all()
    return session.get(Story, story).hidden_at is not None


def test_three_trusted_members_hide_it_until_a_moderator_looks(
    session: Session,
    me: TestClient,
    stranger: TestClient,
    moderator: TestClient,
    reporter,
    story: int,
    outbox: list[dict[str, str]],
) -> None:
    for n in range(2):
        report(reporter(n), story)
    assert not hidden(session, story)

    report(reporter(2), story)

    assert hidden(session, story)
    assert stranger.get(f"/stories/{story}").status_code == 404
    assert me.get(f"/stories/{story}").json()["hidden"] is True
    entry = session.scalars(
        select(ModerationAction).order_by(ModerationAction.id.desc())
    ).first()
    assert (entry.action, entry.actor_id) == ("auto_hide", None)
    recipients = {mail["to"] for mail in outbox}
    assert "proprietaire.test@example.com" in recipients
    assert "modo.test@example.com" in recipients
    author_mail = next(m for m in outbox if m["to"] == "proprietaire.test@example.com")
    assert "pas une sanction" in author_mail["body"]


@pytest.mark.parametrize(
    "untrusted",
    [
        {"age_days": 1},
        {"verified": False},
    ],
)
def test_young_or_unverified_accounts_do_not_count(
    session: Session, reporter, story: int, untrusted: dict
) -> None:
    report(reporter(0), story)
    report(reporter(1), story)

    report(reporter(2, **untrusted), story)

    assert not hidden(session, story)


def test_reporters_judged_abusive_once_no_longer_count(
    session: Session, reporter, story: int, mine: int
) -> None:
    clients = [reporter(n) for n in range(3)]
    abuser = session.scalars(
        select(User).where(User.email == "signaleur2.test@example.com")
    ).one()
    session.add(
        Report(
            reporter_id=abuser.id,
            reason="spam",
            decision="abusive",
            handled_at=datetime.now(UTC),
        )
    )
    session.flush()

    for c in clients:
        report(c, story)

    assert not hidden(session, story)


def test_the_case_comes_first_and_says_so(
    reporter, story: int, moderator: TestClient, stranger: TestClient, mine: int
) -> None:
    stranger.post(
        "/reports",
        json={"target": "character", "target_id": mine, "reason": "spam"},
    )
    for n in range(3):
        report(reporter(n), story)

    first = moderator.get("/moderation/cases").json()["items"][0]

    assert (first["target"], first["target_id"], first["auto_hidden"]) == (
        "story",
        story,
        True,
    )


def test_a_dismissed_case_restores_the_content_and_tells_its_author(
    session: Session,
    reporter,
    story: int,
    moderator: TestClient,
    stranger: TestClient,
    outbox: list[dict[str, str]],
) -> None:
    for n in range(3):
        report(reporter(n), story)

    moderator.post(
        f"/moderation/cases/story/{story}/decide",
        json={"decision": "no_action", **WHY},
    )

    assert not hidden(session, story)
    assert stranger.get(f"/stories/{story}").status_code == 200
    assert "de nouveau visible" in outbox[-1]["subject"]


def test_a_founded_case_stays_hidden(
    session: Session, reporter, story: int, moderator: TestClient
) -> None:
    for n in range(3):
        report(reporter(n), story)

    moderator.post(
        f"/moderation/cases/story/{story}/decide",
        json={"decision": "founded", **WHY},
    )

    assert hidden(session, story)


def test_a_hand_hidden_content_is_not_restored_by_a_dismissal(
    session: Session, stranger: TestClient, story: int, moderator: TestClient
) -> None:
    report(stranger, story)
    moderator.post(f"/moderation/stories/{story}/hide", json=WHY)

    moderator.post(
        f"/moderation/cases/story/{story}/decide",
        json={"decision": "no_action", **WHY},
    )

    assert hidden(session, story)


def test_the_thresholds_can_be_lowered_to_try_it_locally(
    session: Session,
    monkeypatch: pytest.MonkeyPatch,
    reporter,
    story: int,
) -> None:
    monkeypatch.setattr(settings, "auto_hide_reporters", 2)
    monkeypatch.setattr(settings, "auto_hide_min_account_days", 0)

    report(reporter(0, age_days=0), story)
    report(reporter(1, age_days=0), story)

    assert hidden(session, story)
