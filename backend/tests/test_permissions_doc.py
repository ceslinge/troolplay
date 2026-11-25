"""docs/permissions.md est la spécification : chaque ligne de son tableau est vérifiée ici (#56).

Pour chaque action et chaque rôle, on essaie vraiment, contre l'API, et on compare au
« oui » ou « non » du document. Une ligne ajoutée au document sans vérification, ou un
code qui ne fait plus ce que le document dit, et la CI échoue.
"""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.accounts.models import User
from backend.characters.models import Character
from backend.main import app
from backend.servers.models import GameServer
from backend.stories.models import Story

DOC = Path(__file__).resolve().parents[2] / "docs" / "permissions.md"
ROLES = ("Visiteur", "Joueur", "Propriétaire", "Modérateur", "Admin")
WHY = {"reason": "Vérification des permissions."}
TEXT = "Le vent tournait. Encore une nuit sans sommeil, pensa-t-elle."


def read_table() -> dict[str, dict[str, bool]]:
    """Le premier tableau du document : action → rôle → oui / non."""
    rows: dict[str, dict[str, bool]] = {}
    lines = DOC.read_text().splitlines()
    start = next(i for i, line in enumerate(lines) if line.startswith("| Action |"))
    for line in lines[start + 2 :]:
        if not line.startswith("|"):
            break
        cells = [c.strip() for c in line.strip("|").split("|")]
        rows[cells[0]] = {role: cells[i + 1] == "oui" for i, role in enumerate(ROLES)}
    return rows


@dataclass
class World:
    """Le monde où chaque rôle essaie : un propriétaire, son contenu, un compte cible."""

    session: Session
    character: int
    story: int
    draft: int
    hidden: int
    npc: int
    target: int
    server: int


def make_story(me: TestClient, character: int, publish: bool = True) -> int:
    story = me.post(
        "/stories", json={"character_id": character, "title": "La nuit", "body": TEXT}
    ).json()
    if publish:
        me.post(f"/stories/{story['id']}/publish")
    return story["id"]


def owns(client: TestClient, w: World) -> bool:
    """Le propriétaire le sait par ses personnages, l'équipe par sa vue des fiches."""
    mine = client.get("/me/characters")
    if mine.status_code == 200 and any(
        c["id"] == w.character for c in mine.json()["items"]
    ):
        return True
    team = client.get(f"/moderation/characters/{w.character}")
    return team.status_code == 200 and team.json()["owner"] is not None


def ok(response, *codes: int) -> bool:
    return response.status_code in (codes or (200,))


CHECKS: dict[str, Callable[[TestClient, World], bool]] = {
    "Lire une fiche publiée": lambda c, w: ok(c.get(f"/characters/{w.character}")),
    "Lire une histoire publiée": lambda c, w: ok(c.get(f"/stories/{w.story}")),
    "Lire un brouillon": lambda c, w: ok(c.get(f"/stories/{w.draft}")),
    "Lire un contenu masqué": lambda c, w: ok(c.get(f"/stories/{w.hidden}")),
    "Créer personnage ou histoire": lambda c, w: ok(
        c.post(
            "/characters",
            json={"name": "Nouvelle", "server_id": w.server, "gender": "neutral"},
        ),
        201,
    ),
    "Modifier un contenu, ses lieux, son retrait": lambda c, w: ok(
        c.patch(f"/characters/{w.character}", json={"hook": "Assieds-toi."})
    ),
    "Supprimer un contenu": lambda c, w: ok(c.delete(f"/stories/{w.story}"), 204),
    "Signaler": lambda c, w: ok(
        c.post(
            "/reports",
            json={"target": "story", "target_id": w.story, "reason": "spam"},
        ),
        202,
    ),
    "Masquer, traiter un signalement": lambda c, w: ok(
        c.post(f"/moderation/stories/{w.story}/hide", json=WHY)
    ),
    "Suspendre, bannir": lambda c, w: ok(
        c.post(
            f"/moderation/accounts/{w.target}/suspend",
            json={"duration": "day", **WHY},
        )
    ),
    "Retirer le droit de signaler": lambda c, w: ok(
        c.post(
            f"/moderation/accounts/{w.target}/reporting",
            json={"allowed": False, **WHY},
        )
    ),
    "Lire le journal de modération": lambda c, w: ok(c.get("/moderation/journal")),
    "Savoir quel compte possède un personnage": owns,
    "Exporter ses données": lambda c, w: ok(c.get("/me/export")),
    "Gérer les PNJ": lambda c, w: ok(
        c.post(f"/moderation/characters/{w.npc}/hide", json=WHY)
    ),
    "Gérer les serveurs": lambda c, w: ok(
        c.post(f"/moderation/servers/{w.server}/close", json=WHY)
    ),
    "Nommer modérateurs et admins": lambda c, w: ok(
        c.post(
            f"/moderation/accounts/{w.target}/role",
            json={"role": "moderator", **WHY},
        )
    ),
}

TABLE = read_table()


def test_every_line_of_the_document_is_checked() -> None:
    assert set(TABLE) == set(CHECKS)


@pytest.fixture
def world(
    session: Session, me: TestClient, mine: int, server: GameServer, make_member
) -> World:
    hidden = make_story(me, mine)
    session.get(Story, hidden).hidden_at = datetime.now(UTC)
    npc = Character(user_id=None, server_id=None, is_npc=True, name="Gardien")
    session.add(npc)
    target: User = make_member("cible.test@example.com")
    session.flush()
    return World(
        session=session,
        character=mine,
        story=make_story(me, mine),
        draft=make_story(me, mine, publish=False),
        hidden=hidden,
        npc=npc.id,
        target=target.id,
        server=server.id,
    )


FIXTURE_OF = {
    "Joueur": "stranger",
    "Propriétaire": "me",
    "Modérateur": "moderator",
    "Admin": "admin",
}


@pytest.mark.parametrize(
    ("action", "role"), [(action, role) for action in TABLE for role in ROLES]
)
def test_the_document_says_what_the_code_does(
    request: pytest.FixtureRequest, action: str, role: str, world: World
) -> None:
    if role == "Visiteur":
        with TestClient(app) as visitor:
            allowed = CHECKS[action](visitor, world)
    else:
        allowed = CHECKS[action](request.getfixturevalue(FIXTURE_OF[role]), world)

    assert allowed == TABLE[action][role], (
        f"docs/permissions.md dit « {'oui' if TABLE[action][role] else 'non'} » "
        f"pour « {action} » ({role})"
    )
