"""Exporter ses données (#55) : tout ce que le site garde de moi, en un fichier JSON.

Lisible par une machine (droit à la portabilité) comme par un humain. Rien sur les autres :
ni le compte que j'ai signalé, ni la copie de son contenu, ni qui, dans l'équipe, a décidé
ou répondu. Les colonnes viennent des modèles : un champ ajouté plus tard y entre tout seul.
Ouvert aussi à un compte suspendu : le droit d'accès ne dépend pas d'une suspension.
"""

from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import APIRouter
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlalchemy import inspect, select

from backend.accounts.models import User
from backend.accounts.sessions import SessionUser
from backend.accounts.throttle import throttle
from backend.characters.models import Character
from backend.db import SessionDep
from backend.ignores.models import IgnoredCharacter
from backend.moderation.models import Contest, ModerationAction, Report
from backend.stories.models import Story
from backend.support.models import Conversation

router = APIRouter(prefix="/me", tags=["accounts"])

EXPORT_LIMIT = 10
EXPORT_WINDOW = timedelta(days=1)

# Ce qui ne m'appartient pas, ou ne dit rien de moi : des secrets, d'autres comptes.
SECRETS = {"password_hash", "token_hash"}
OTHERS = {
    "user_id",
    "actor_id",
    "author_id",
    "answered_by",
    "handled_by",
    "reporter_id",
    "reported_user_id",
    "target_user_id",
    "snapshot",
}


def row(obj: Any) -> dict[str, Any]:
    """Les colonnes d'une ligne, sans secret ni trace d'un autre compte."""
    return {
        column.key: getattr(obj, column.key)
        for column in inspect(obj).mapper.column_attrs
        if column.key not in SECRETS | OTHERS
    }


def export(session, user: User) -> dict[str, Any]:
    characters = session.scalars(
        select(Character)
        .where(Character.user_id == user.id)
        .order_by(Character.position)
    ).all()
    ignored = session.scalars(
        select(IgnoredCharacter).where(IgnoredCharacter.user_id == user.id)
    ).all()
    decisions = session.scalars(
        select(ModerationAction)
        .where(ModerationAction.target_user_id == user.id)
        .order_by(ModerationAction.created_at)
    ).all()
    conversations = session.scalars(
        select(Conversation)
        .where(Conversation.user_id == user.id)
        .order_by(Conversation.created_at)
    ).all()
    return {
        "exported_at": datetime.now(UTC),
        "account": row(user),
        "characters": [
            row(c) | {"hangouts": [row(h) for h in c.hangouts]} for c in characters
        ],
        "stories": [
            row(s)
            for s in session.scalars(
                select(Story).where(Story.user_id == user.id).order_by(Story.created_at)
            )
        ],
        "ignored_characters": [
            row(i) | {"name": session.get(Character, i.character_id).name}
            for i in ignored
        ],
        "reports_sent": [
            row(r)
            for r in session.scalars(
                select(Report)
                .where(Report.reporter_id == user.id)
                .order_by(Report.created_at)
            )
        ],
        "decisions_about_me": [row(d) for d in decisions],
        "contests": [
            row(c)
            for c in session.scalars(
                select(Contest)
                .where(Contest.user_id == user.id)
                .order_by(Contest.created_at)
            )
        ],
        "requests_to_the_team": [
            row(c) | {"messages": [row(m) for m in c.messages]} for c in conversations
        ],
    }


@router.get("/export")
def export_my_data(user: SessionUser, session: SessionDep) -> JSONResponse:
    """Le fichier, à télécharger : ce que le site garde de moi."""
    throttle(session, "export", str(user.id), limit=EXPORT_LIMIT, window=EXPORT_WINDOW)
    session.commit()
    day = datetime.now(UTC).date().isoformat()
    return JSONResponse(
        jsonable_encoder(export(session, user)),
        headers={
            "Content-Disposition": f'attachment; filename="troolplay-mes-donnees-{day}.json"'
        },
    )
