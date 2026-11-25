from datetime import UTC, datetime, timedelta
from typing import Annotated
from zoneinfo import ZoneInfo

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Cookie,
    HTTPException,
    Request,
    Response,
)
from sqlalchemy import delete, func, or_, select
from sqlalchemy.orm import Session

from backend.accounts import emails
from backend.accounts.models import LoginFailure, ThrottleEvent, User
from backend.accounts.roles import capabilities
from backend.accounts.schemas import (
    AccountDeletionIn,
    EmailIn,
    LoginIn,
    MeOut,
    Message,
    PasswordChangeIn,
    PasswordResetIn,
    SignupIn,
    TokenIn,
)
from backend.accounts.security import hash_password, verify_password
from backend.accounts.sessions import (
    COOKIE_NAME,
    CurrentUser,
    SessionUser,
    close_all_sessions,
    close_session,
    open_session,
)
from backend.accounts.throttle import throttle
from backend.accounts.tokens import issue_token, use_token
from backend.config import settings
from backend.db import SessionDep

PARIS = ZoneInfo("Europe/Paris")

router = APIRouter(tags=["accounts"])

FAILURE_WINDOW = timedelta(minutes=15)
MAX_FAILURES_PER_EMAIL = 5
MAX_FAILURES_PER_IP = 20
WRONG_CREDENTIALS = "Email ou mot de passe incorrect"


def client_ip(request: Request) -> str:
    return request.client.host if request.client else "inconnue"


def find_user(session: Session, email: str) -> User | None:
    return session.scalars(
        select(User).where(func.lower(User.email) == email.lower())
    ).one_or_none()


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
    # Un compte suspendu se connecte quand même, pour lire la décision et la contester
    # (#141) : current_user lui ferme toutes les autres routes.

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
def read_me(user: SessionUser) -> MeOut:
    suspended = user.suspended()
    return MeOut(
        email=user.email,
        role=user.role,
        created_at=user.created_at,
        # Pour que le site montre les bons boutons. Chaque route revérifie de son côté.
        capabilities=sorted(capabilities(user)),
        suspended=suspended,
        suspended_until=user.banned_until if suspended else None,
    )


SIGNUP_SENT = "Si cette adresse est libre, un lien de vérification vient de partir."
RESEND_SENT = (
    "Si cette adresse attend sa vérification, un nouveau lien vient de partir."
)


def verification_email(token: str) -> tuple[str, str]:
    link = f"{settings.site_url}/verifier?jeton={token}"
    return (
        "Bienvenue sur le panneau : vérifie ton adresse",
        (
            "Pour finir ton inscription, ouvre ce lien dans les 24 heures :\n\n"
            f"{link}\n\nSi tu n'as rien demandé, ignore ce message."
        ),
    )


@router.post("/accounts", status_code=202)
def sign_up(
    data: SignupIn, request: Request, session: SessionDep, background: BackgroundTasks
) -> Message:
    throttle(session, "signup", client_ip(request), limit=5, window=timedelta(hours=1))
    # On hache toujours, même si l'adresse est prise :
    # la réponse prend le même temps, et ne trahit pas qui est inscrit.
    password_hash = hash_password(data.password)
    user = find_user(session, data.email)

    if user is None:
        user = User(email=data.email.lower(), password_hash=password_hash)
        session.add(user)
        session.flush()
        token = issue_token(session, user, "verify")
        session.commit()
        background.add_task(emails.send_email, user.email, *verification_email(token))
    elif user.email_verified_at is None:
        token = issue_token(session, user, "verify")
        session.commit()
        background.add_task(emails.send_email, user.email, *verification_email(token))
    else:
        session.commit()
        background.add_task(
            emails.send_email,
            user.email,
            "Quelqu'un a voulu s'inscrire avec ton adresse",
            "Une inscription vient d'être tentée avec ton adresse, qui a déjà un compte.\n\n"
            "Si c'était toi, connecte-toi simplement. Mot de passe oublié ? "
            f"Tu peux le changer depuis {settings.site_url}.\n\n"
            "Si ce n'était pas toi, rien n'a changé : ton compte est intact.",
        )
    return Message(detail=SIGNUP_SENT)


@router.post("/accounts/verify", status_code=204)
def verify_email(data: TokenIn, session: SessionDep) -> None:
    user = use_token(session, data.token, "verify")
    if user is None:
        raise HTTPException(status_code=400, detail="Ce lien n'est plus valable")
    if user.email_verified_at is None:
        user.email_verified_at = datetime.now(UTC)
    session.commit()


@router.post("/accounts/verify/resend", status_code=202)
def resend_verification(
    data: EmailIn, session: SessionDep, background: BackgroundTasks
) -> Message:
    email = data.email.lower()
    throttle(session, "resend", email, limit=3, window=timedelta(hours=1))
    user = find_user(session, email)
    if user is not None and user.email_verified_at is None:
        token = issue_token(session, user, "verify")
        session.commit()
        background.add_task(emails.send_email, user.email, *verification_email(token))
    else:
        session.commit()
    return Message(detail=RESEND_SENT)


FORGOT_SENT = "Si cette adresse a un compte, un lien pour changer de mot de passe vient de partir."


@router.post("/password/forgot", status_code=202)
def forgot_password(
    data: EmailIn, session: SessionDep, background: BackgroundTasks
) -> Message:
    email = data.email.lower()
    throttle(session, "forgot", email, limit=3, window=timedelta(hours=1))
    user = find_user(session, email)
    if user is not None and not user.suspended():
        token = issue_token(session, user, "reset")
        session.commit()
        link = f"{settings.site_url}/mot-de-passe?jeton={token}"
        background.add_task(
            emails.send_email,
            user.email,
            "Changer ton mot de passe",
            "Pour choisir un nouveau mot de passe, ouvre ce lien dans l'heure :\n\n"
            f"{link}\n\n"
            "Si tu n'as rien demandé, ignore ce message : ton mot de passe ne change pas.",
        )
    else:
        session.commit()
    return Message(detail=FORGOT_SENT)


@router.post("/password/reset", status_code=204)
def reset_password(data: PasswordResetIn, session: SessionDep) -> None:
    user = use_token(session, data.token, "reset")
    if user is None:
        raise HTTPException(status_code=400, detail="Ce lien n'est plus valable")
    user.password_hash = hash_password(data.password)
    # Le lien est arrivé dans sa boîte : l'adresse est donc bien la sienne.
    if user.email_verified_at is None:
        user.email_verified_at = datetime.now(UTC)
    # Si quelqu'un d'autre était connecté, il ne l'est plus.
    close_all_sessions(session, user)
    session.commit()


@router.patch("/me/password", status_code=204)
def change_password(
    data: PasswordChangeIn,
    user: CurrentUser,
    session: SessionDep,
    token: Annotated[str | None, Cookie(alias=COOKIE_NAME)] = None,
) -> None:
    if not verify_password(data.current_password, user.password_hash):
        raise HTTPException(status_code=403, detail="Mot de passe actuel incorrect")
    user.password_hash = hash_password(data.new_password)
    close_all_sessions(session, user, keep_token=token)
    session.commit()


@router.delete("/me", status_code=204)
def delete_account(
    data: AccountDeletionIn,
    user: CurrentUser,
    response: Response,
    session: SessionDep,
    token: Annotated[str | None, Cookie(alias=COOKIE_NAME)] = None,
) -> None:
    if not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=403, detail="Mot de passe incorrect")
    email = user.email.lower()
    user_id = user.id
    # La base supprime en cascade ses personnages, leurs lieux, ses sessions et ses liens.
    session.delete(user)
    # L'adresse reste aussi dans les traces des limites : on les efface avec le compte.
    session.execute(delete(LoginFailure).where(LoginFailure.email == email))
    session.execute(delete(ThrottleEvent).where(ThrottleEvent.key == email))
    # Les limites comptées par compte (histoires, signalements) partent avec lui.
    session.execute(delete(ThrottleEvent).where(ThrottleEvent.key == str(user_id)))
    close_session(session, token, response)
    session.commit()
