import json
from datetime import UTC, datetime

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.accounts.models import User
from backend.characters.models import CharacterHangout

TEXT = "Le vent tournait. Encore une nuit sans sommeil, pensa-t-elle."
WHY = {"reason": "Vise un joueur précis, contraire à la charte."}
# Ce qu'un export ne contient jamais : des secrets, ou un autre compte.
NEVER = (
    "password_hash",
    "token_hash",
    "actor_id",
    "author_id",
    "answered_by",
    "handled_by",
    "reported_user_id",
    "snapshot",
)


def keys(value) -> set[str]:
    if isinstance(value, dict):
        return set(value) | {k for v in value.values() for k in keys(v)}
    if isinstance(value, list):
        return {k for v in value for k in keys(v)}
    return set()


def test_i_download_what_the_site_keeps_about_me(
    session: Session,
    me: TestClient,
    owner: User,
    stranger: TestClient,
    moderator: TestClient,
    mine: int,
) -> None:
    session.add(CharacterHangout(character_id=mine, area="Astrub", x=5, y=-18))
    session.flush()
    story = me.post(
        "/stories", json={"character_id": mine, "title": "La nuit", "body": TEXT}
    ).json()
    me.post(f"/stories/{story['id']}/publish")
    me.post("/stories", json={"character_id": mine, "title": "Brouillon", "body": ""})
    theirs = stranger.post(
        "/characters",
        json={
            "name": "Voisine",
            "server_id": me.get(f"/characters/{mine}").json()["server"]["id"],
            "gender": "feminine",
        },
    ).json()
    me.put(f"/me/ignored/{theirs['id']}")
    stranger_story = stranger.post(
        "/stories",
        json={"character_id": theirs["id"], "title": "Ailleurs", "body": TEXT},
    ).json()
    stranger.post(f"/stories/{stranger_story['id']}/publish")
    me.post(
        "/reports",
        json={"target": "story", "target_id": stranger_story["id"], "reason": "spam"},
    )
    moderator.post(f"/moderation/stories/{story['id']}/hide", json=WHY)
    decision = me.get("/me/decisions").json()["items"][0]
    me.post(
        f"/me/decisions/{decision['id']}/contest",
        json={"body": "Je ne visais personne, c'est inventé."},
    )
    request = me.post(
        "/me/conversations",
        json={"topic": "question", "body": "Comment ranger mes histoires ?"},
    ).json()
    moderator.post(
        f"/moderation/conversations/{request['id']}/messages",
        json={"body": "Depuis ta fiche, bientôt."},
    )

    response = me.get("/me/export")
    data = response.json()

    assert response.status_code == 200
    assert response.headers["content-disposition"].startswith(
        'attachment; filename="troolplay-mes-donnees-'
    )
    assert data["account"]["email"] == owner.email
    assert data["characters"][0]["hangouts"][0]["area"] == "Astrub"
    assert {s["title"] for s in data["stories"]} == {"La nuit", "Brouillon"}
    assert data["ignored_characters"][0]["name"] == "Voisine"
    assert data["reports_sent"][0]["reason"] == "spam"
    assert data["decisions_about_me"][0]["action"] == "hide"
    assert data["contests"][0]["body"].startswith("Je ne visais")
    assert [m["from_team"] for m in data["requests_to_the_team"][0]["messages"]] == [
        False,
        True,
    ]
    assert not keys(data) & set(NEVER)
    assert "Voisine" not in json.dumps(data["characters"])


def test_nothing_of_anyone_else(
    me: TestClient, stranger: TestClient, mine: int
) -> None:
    data = stranger.get("/me/export").json()

    assert data["characters"] == []
    assert data["stories"] == []


def test_a_visitor_has_nothing_to_export(client: TestClient) -> None:
    assert client.get("/me/export").status_code == 401


def test_a_suspended_member_can_still_take_their_data(
    session: Session, me: TestClient, owner: User
) -> None:
    owner.banned_at = datetime.now(UTC)
    session.flush()

    assert me.get("/me/export").status_code == 200


def test_exports_are_counted(me: TestClient) -> None:
    statuses = [me.get("/me/export").status_code for _ in range(11)]

    assert statuses[:10] == [200] * 10
    assert statuses[10] == 429
