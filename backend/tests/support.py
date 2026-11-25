"""Ce que plusieurs fichiers de test partagent, hors fixtures."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.moderation.models import ModerationAction


def journal(session: Session) -> list[ModerationAction]:
    """Les lignes du journal de modération, de la plus ancienne à la plus récente."""
    return list(session.scalars(select(ModerationAction).order_by(ModerationAction.id)))
