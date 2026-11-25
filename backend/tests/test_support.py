from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.accounts.models import User
from backend.support.models import Conversation

ASK = {"topic": "question", "body": "Comment changer le serveur de ma fiche ?"}
ANSWER = {"body": "Depuis la fiche : Modifier, puis le menu Serveur."}


def start(client: TestClient, body: dict = ASK) -> dict:
    response = client.post("/me/conversations", json=body)
    assert response.status_code == 201
    return response.json()


def test_a_member_writes_to_the_team(me: TestClient) -> None:
    conversation = start(me)

    assert conversation["topic"] == "question"
    assert conversation["waiting_for_team"] is True
    assert [m["from_team"] for m in conversation["messages"]] == [False]
    assert me.get("/me/conversations").json()["items"][0]["id"] == conversation["id"]


def test_the_team_answers_and_the_member_is_told(
    me: TestClient, moderator: TestClient, outbox: list[dict[str, str]]
) -> None:
    conversation = start(me)
    waiting = moderator.get("/moderation/conversations").json()

    answered = moderator.post(
        f"/moderation/conversations/{conversation['id']}/messages", json=ANSWER
    )

    assert waiting["total"] == 1
    assert answered.status_code == 201
    assert answered.json()["messages"][-1]["author_id"] is not None
    assert moderator.get("/moderation/conversations").json()["total"] == 0
    assert (
        moderator.get("/moderation/conversations?status=answered").json()["total"] == 1
    )
    assert outbox[-1]["subject"] == "L'équipe t'a répondu"
    assert ANSWER["body"] not in outbox[-1]["body"]
    seen = me.get("/me/conversations").json()["items"][0]
    assert seen["messages"][-1]["from_team"] is True
    assert "author_id" not in seen["messages"][-1]


def test_the_member_follows_up_until_it_is_closed(
    me: TestClient, moderator: TestClient
) -> None:
    conversation = start(me)
    url = f"/me/conversations/{conversation['id']}/messages"
    moderator.post(
        f"/moderation/conversations/{conversation['id']}/messages", json=ANSWER
    )

    again = me.post(url, json={"body": "Merci, et pour le nom en jeu ?"})
    moderator.post(f"/moderation/conversations/{conversation['id']}/close")
    late = me.post(url, json={"body": "Encore une petite question."})

    assert again.json()["waiting_for_team"] is True
    assert late.status_code == 409
    assert moderator.get("/moderation/conversations?status=closed").json()["total"] == 1


def test_a_few_open_requests_at_a_time(me: TestClient) -> None:
    for _ in range(3):
        start(me)

    assert me.post("/me/conversations", json=ASK).status_code == 409


def test_messages_are_counted(me: TestClient) -> None:
    conversation = start(me)
    url = f"/me/conversations/{conversation['id']}/messages"
    # Le premier message compte déjà : neuf réponses passent, la dixième non.
    statuses = [me.post(url, json={"body": ASK["body"]}).status_code for _ in range(10)]

    assert statuses[:9] == [201] * 9
    assert statuses[9] == 429


def test_one_sees_only_ones_own_conversations(
    me: TestClient, stranger: TestClient
) -> None:
    conversation = start(me)

    assert stranger.get("/me/conversations").json()["items"] == []
    assert (
        stranger.post(
            f"/me/conversations/{conversation['id']}/messages", json=ANSWER
        ).status_code
        == 404
    )


def test_the_team_tools_are_for_the_team(me: TestClient) -> None:
    conversation = start(me)

    assert me.get("/moderation/conversations").status_code == 403
    assert (
        me.post(
            f"/moderation/conversations/{conversation['id']}/messages", json=ANSWER
        ).status_code
        == 403
    )
    assert (
        me.post(f"/moderation/conversations/{conversation['id']}/close").status_code
        == 403
    )


def test_closed_conversations_fade_after_a_year(
    session: Session, me: TestClient, moderator: TestClient
) -> None:
    old = start(me)
    moderator.post(f"/moderation/conversations/{old['id']}/close")
    session.get(Conversation, old["id"]).closed_at = datetime.now(UTC) - timedelta(
        days=400
    )
    session.flush()

    assert me.get("/me/conversations").json()["items"] == []


def test_they_leave_with_the_account(
    session: Session, me: TestClient, owner: User, member_password: str
) -> None:
    start(me)

    me.request("DELETE", "/me", json={"password": member_password})

    assert session.scalar(select(func.count()).select_from(Conversation)) == 0
