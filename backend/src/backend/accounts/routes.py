from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Cookie, HTTPException, Request, Response
from sqlalchemy import delete, func, or_, select

from backend.accounts.models import LoginFailure, User
from backend.accounts.schemas import LoginIn, MeOut
from backend.accounts.security import verify_password
from backend.accounts.sessions import (
    COOKIE_NAME,
    CurrentUser,
    close_session,
    open_session,
)
from backend.db import SessionDep

router = APIRouter(tags=["accounts"])

FAILURE_WINDOW = timedelta(minutes=15)
MAX_FAILURES_PER_EMAIL = 5
MAX_FAILURES_PER_IP = 20
WRONG_CREDENTIALS = "Email ou mot de passe incorrect"


def client_ip(request: Request) -> str:
    return request.client.host if request.client else "inconnue"


@router.post("/session", status_code=204)
def log_in(
    credentials: LoginIn, request: Request, response: Response, session: SessionDep
) -> None:
    email = credentials.email.lower()
    ip = client_ip(request)
    since = datetime.now(UTC) - FAILURE_WINDOW

    by_email = func.count().filter(LoginFailure.email == email)
    by_ip = func.count().filter(LoginFailure.ip == ip)
    failures_by_email, failures_by_ip = session.execute(
        select(by_email, by_ip).where(
            LoginFailure.created_at > since,
            or_(LoginFailure.email == email, LoginFailure.ip == ip),
        )
    ).one()
    if (
        failures_by_email >= MAX_FAILURES_PER_EMAIL
        or failures_by_ip >= MAX_FAILURES_PER_IP
    ):
        raise HTTPException(
            status_code=429,
            detail="Trop d'essais. Réessaie dans un quart d'heure.",
            headers={"Retry-After": str(int(FAILURE_WINDOW.total_seconds()))},
        )

    user = session.scalars(
        select(User).where(func.lower(User.email) == email)
    ).one_or_none()
    if not verify_password(credentials.password, user.password_hash if user else None):
        session.add(LoginFailure(email=email, ip=ip))
        session.commit()
        raise HTTPException(status_code=401, detail=WRONG_CREDENTIALS)

    # Le mot de passe est bon : on peut dire pourquoi la connexion est refusée.
    if user.email_verified_at is None:
        raise HTTPException(status_code=403, detail="Vérifie d'abord ton adresse email")
    if user.banned_at is not None:
        raise HTTPException(status_code=403, detail="Ce compte est suspendu")

    session.execute(delete(LoginFailure).where(LoginFailure.email == email))
    open_session(session, user, response)
    session.commit()


@router.delete("/session", status_code=204)
def log_out(
    response: Response,
    session: SessionDep,
    token: Annotated[str | None, Cookie(alias=COOKIE_NAME)] = None,
) -> None:
    close_session(session, token, response)
    session.commit()


@router.get("/me")
def read_me(user: CurrentUser) -> MeOut:
    return MeOut.model_validate(user)
