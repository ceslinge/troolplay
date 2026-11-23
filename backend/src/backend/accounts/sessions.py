"""Ouvrir, retrouver et fermer les sessions."""

from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import Cookie, Depends, HTTPException, Response
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from backend.accounts.models import User, UserSession
from backend.accounts.security import new_token, token_hash
from backend.config import settings
from backend.db import SessionDep

COOKIE_NAME = "session"
SESSION_LIFETIME = timedelta(days=30)
# On ne prolonge pas la session à chaque requête, seulement une fois par jour :
# ça évite une écriture en base à chaque page vue.
REFRESH_AFTER = timedelta(days=1)


def open_session(session: Session, user: User, response: Response) -> None:
    token = new_token()
    now = datetime.now(UTC)
    session.add(
        UserSession(
            user_id=user.id,
            token_hash=token_hash(token),
            last_seen_at=now,
            expires_at=now + SESSION_LIFETIME,
        )
    )
    response.set_cookie(
        COOKIE_NAME,
        token,
        max_age=int(SESSION_LIFETIME.total_seconds()),
        path="/",
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
    )


def close_session(session: Session, token: str | None, response: Response) -> None:
    if token:
        session.execute(
            delete(UserSession).where(UserSession.token_hash == token_hash(token))
        )
    response.delete_cookie(
        COOKIE_NAME,
        path="/",
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
    )


def close_all_sessions(
    session: Session, user: User, keep_token: str | None = None
) -> None:
    """Déconnecte le compte partout, sauf de la session qu'on garde."""
    query = delete(UserSession).where(UserSession.user_id == user.id)
    if keep_token:
        query = query.where(UserSession.token_hash != token_hash(keep_token))
    session.execute(query)


def current_user(
    session: SessionDep,
    token: Annotated[str | None, Cookie(alias=COOKIE_NAME)] = None,
) -> User:
    """La personne connectée, ou 401. À utiliser dans toute route qui l'exige."""
    if not token:
        raise HTTPException(status_code=401, detail="Il faut être connecté")
    now = datetime.now(UTC)
    found = session.execute(
        select(UserSession, User)
        .join(User, User.id == UserSession.user_id)
        .where(
            UserSession.token_hash == token_hash(token), UserSession.expires_at > now
        )
    ).one_or_none()
    if found is None:
        raise HTTPException(status_code=401, detail="Il faut être connecté")
    user_session, user = found
    if user.banned_at is not None:
        raise HTTPException(status_code=401, detail="Il faut être connecté")
    if now - user_session.last_seen_at > REFRESH_AFTER:
        user_session.last_seen_at = now
        user_session.expires_at = now + SESSION_LIFETIME
        session.commit()
    return user


CurrentUser = Annotated[User, Depends(current_user)]


def optional_user(
    session: SessionDep,
    token: Annotated[str | None, Cookie(alias=COOKIE_NAME)] = None,
) -> User | None:
    """La personne connectée, ou None pour un visiteur. Ne refuse jamais."""
    if not token:
        return None
    try:
        return current_user(session, token)
    except HTTPException:
        return None


OptionalUser = Annotated[User | None, Depends(optional_user)]
