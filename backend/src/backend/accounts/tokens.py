"""Les liens envoyés par email : à usage unique, de courte durée, stockés en empreinte."""

from datetime import UTC, datetime, timedelta

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from backend.accounts.models import EmailToken, User
from backend.accounts.security import new_token, token_hash

LIFETIMES = {"verify": timedelta(hours=24), "reset": timedelta(hours=1)}


def issue_token(session: Session, user: User, purpose: str) -> str:
    """Crée un jeton et renvoie sa valeur, la seule fois où on la connaît."""
    token = new_token()
    session.add(
        EmailToken(
            user_id=user.id,
            purpose=purpose,
            token_hash=token_hash(token),
            expires_at=datetime.now(UTC) + LIFETIMES[purpose],
        )
    )
    return token


def use_token(session: Session, token: str, purpose: str) -> User | None:
    """Consomme un jeton valide et renvoie son compte, ou None s'il ne vaut rien."""
    now = datetime.now(UTC)
    found = session.scalars(
        select(EmailToken).where(
            EmailToken.token_hash == token_hash(token),
            EmailToken.purpose == purpose,
            EmailToken.used_at.is_(None),
            EmailToken.expires_at > now,
        )
    ).one_or_none()
    if found is None:
        return None
    # Un lien utilisé rend caducs les autres liens du même genre, encore en circulation.
    session.execute(
        update(EmailToken)
        .where(
            EmailToken.user_id == found.user_id,
            EmailToken.purpose == purpose,
            EmailToken.used_at.is_(None),
        )
        .values(used_at=now)
    )
    return session.get(User, found.user_id)
