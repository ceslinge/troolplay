from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from support import journal

from backend.accounts.models import User
from backend.stories.models import Story

TEXT = "Le vent tournait. Encore une nuit sans sommeil, pensa-t-elle."
WHY = {"reason": "Vise un joueur précis, contraire à la charte."}
CONTEST = {"body": "Je ne visais personne : c'est une scène de taverne inventée."}


def publish(me: TestClient, character: int) -> int:
    story = me.post(
        "/stories", json={"character_id": character, "title": "La nuit", "body": TEXT}
    ).json()
    me.post(f"/stories/{story['id']}/publish")
    return story["id"]


def hide(moderator: TestClient, story: int) -> int:
    """Masque l'histoire et renvoie la décision, telle que la voit son auteur."""
    moderator.post(f"/moderation/stories/{story}/hide", json=WHY)
    return story


def only_decision(me: TestClient) -> dict:
    items = me.get("/me/decisions").json()["items"]
    assert len(items) == 1
    return items[0]


def test_i_see_the_decisions_about_me_without_who_took_them(
    me: TestClient, moderator: TestClient, mine: int
) -> None:
    hide(moderator, publish(me, mine))

    decision = only_decision(me)

    assert decision["action"] == "hide"
    assert decision["reason"] == WHY["reason"]
    assert decision["target_name"] == "La nuit"
    assert decision["contest"] is None
    assert "actor_id" not in decision


def test_a_decision_is_contested_once(
    me: TestClient, moderator: TestClient, mine: int
) -> None:
    hide(moderator, publish(me, mine))
    decision = only_decision(me)

    first = me.post(f"/me/decisions/{decision['id']}/contest", json=CONTEST)
    again = me.post(f"/me/decisions/{decision['id']}/contest", json=CONTEST)

    assert first.status_code == 201
    assert first.json()["contest"]["body"] == CONTEST["body"]
    assert again.status_code == 409


def test_one_contests_only_ones_own_decisions(
    me: TestClient, stranger: TestClient, moderator: TestClient, mine: int
) -> None:
    hide(moderator, publish(me, mine))
    decision = only_decision(me)

    assert (
        stranger.post(
            f"/me/decisions/{decision['id']}/contest", json=CONTEST
        ).status_code
        == 404
    )
    assert stranger.get("/me/decisions").json()["items"] == []


def test_a_contest_says_something(
    me: TestClient, moderator: TestClient, mine: int
) -> None:
    hide(moderator, publish(me, mine))
    decision = only_decision(me)

    blank = me.post(f"/me/decisions/{decision['id']}/contest", json={"body": " " * 20})

    assert blank.status_code == 422


def test_a_role_change_is_not_a_decision_to_contest(
    me: TestClient, owner: User, admin: TestClient
) -> None:
    admin.post(
        f"/moderation/accounts/{owner.id}/role", json={"role": "moderator", **WHY}
    )

    assert me.get("/me/decisions").json()["items"] == []


def test_a_suspended_member_logs_in_to_contest(
    me: TestClient,
    owner: User,
    moderator: TestClient,
    member_password: str,
    outbox: list[dict[str, str]],
) -> None:
    moderator.post(
        f"/moderation/accounts/{owner.id}/suspend", json={"duration": "week", **WHY}
    )
    me.post("/session", json={"email": owner.email, "password": member_password})

    decision = only_decision(me)
    contested = me.post(f"/me/decisions/{decision['id']}/contest", json=CONTEST)

    assert decision["action"] == "suspend"
    assert decision["detail"] == "week"
    assert contested.status_code == 201


def test_the_team_answers_once_and_the_member_is_told(
    session: Session,
    me: TestClient,
    moderator: TestClient,
    mine: int,
    outbox: list[dict[str, str]],
) -> None:
    story = hide(moderator, publish(me, mine))
    me.post(f"/me/decisions/{only_decision(me)['id']}/contest", json=CONTEST)
    waiting = moderator.get("/moderation/contests").json()
    contest = waiting["items"][0]

    answer = {
        "answer": "La scène vise un joueur nommé : on maintient.",
        "outcome": "upheld",
    }
    response = moderator.post(
        f"/moderation/contests/{contest['id']}/answer", json=answer
    )
    again = moderator.post(f"/moderation/contests/{contest['id']}/answer", json=answer)

    assert waiting["total"] == 1
    assert contest["decided_by_me"] is True
    assert response.status_code == 200
    assert again.status_code == 409
    assert session.get(Story, story).hidden_at is not None
    assert moderator.get("/moderation/contests").json()["total"] == 0
    assert journal(session)[-1].action == "answer_contest"
    assert journal(session)[-1].detail == "upheld"
    assert "contestation" in outbox[-1]["subject"]
    assert "maintenue" in outbox[-1]["body"]
    assert only_decision(me)["contest"]["outcome"] == "upheld"


def test_lifting_unhides_the_content(
    session: Session, me: TestClient, moderator: TestClient, mine: int
) -> None:
    story = hide(moderator, publish(me, mine))
    me.post(f"/me/decisions/{only_decision(me)['id']}/contest", json=CONTEST)
    contest = moderator.get("/moderation/contests").json()["items"][0]

    moderator.post(
        f"/moderation/contests/{contest['id']}/answer",
        json={"answer": "Relu : rien à reprocher.", "outcome": "lifted"},
    )

    assert session.get(Story, story).hidden_at is None
    assert [e.action for e in journal(session)[-2:]] == ["unhide", "answer_contest"]


def test_lifting_a_suspension_reinstates_the_account(
    session: Session,
    me: TestClient,
    owner: User,
    moderator: TestClient,
    member_password: str,
) -> None:
    moderator.post(
        f"/moderation/accounts/{owner.id}/suspend", json={"duration": "forever", **WHY}
    )
    me.post("/session", json={"email": owner.email, "password": member_password})
    me.post(f"/me/decisions/{only_decision(me)['id']}/contest", json=CONTEST)
    contest = moderator.get("/moderation/contests").json()["items"][0]

    moderator.post(
        f"/moderation/contests/{contest['id']}/answer",
        json={"answer": "Erreur de compte, désolé.", "outcome": "lifted"},
    )

    session.refresh(owner)
    assert owner.suspended() is False
    assert me.get("/me/characters").status_code == 200
    assert "reinstate" in [e.action for e in journal(session)]


def test_contests_are_for_the_team(me: TestClient) -> None:
    assert me.get("/moderation/contests").status_code == 403
    assert (
        me.post(
            "/moderation/contests/1/answer",
            json={"answer": "Non.", "outcome": "lifted"},
        ).status_code
        == 403
    )


def test_a_moderator_does_not_answer_a_peer(
    session: Session,
    moderator: TestClient,
    admin: TestClient,
    make_member,
    log_in_as,
    client: TestClient,
) -> None:
    peer = make_member("pair.test@example.com", role="moderator")
    admin.post(
        f"/moderation/accounts/{peer.id}/suspend", json={"duration": "day", **WHY}
    )
    log_in_as(client, peer)
    decision = client.get("/me/decisions").json()["items"][0]
    client.post(f"/me/decisions/{decision['id']}/contest", json=CONTEST)
    contest = admin.get("/moderation/contests").json()["items"][0]

    by_peer = moderator.post(
        f"/moderation/contests/{contest['id']}/answer",
        json={"answer": "Je maintiens.", "outcome": "upheld"},
    )

    assert by_peer.status_code == 403
