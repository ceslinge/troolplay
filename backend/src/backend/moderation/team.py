"""Les outils de l'équipe : dossiers de signalements, masquer, suspendre, journal.

Chaque route demande une capacité (accounts/roles.py). On n'agit que sur quelqu'un de rang
inférieur au sien. Chaque action est inscrite au journal, et la personne concernée reçoit
la raison par email.
"""

from collections import Counter
from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from sqlalchemy import Select, delete, func, select
from sqlalchemy.orm import Session, selectinload

from backend.accounts import emails
from backend.accounts.models import User, UserSession
from backend.accounts.roles import (
    Capability,
    LastAdminError,
    Role,
    can,
    outranks,
    require,
    set_role,
)
from backend.accounts.routes import PARIS
from backend.characters.models import Character
from backend.config import settings
from backend.db import SessionDep
from backend.moderation.auto import was_auto_hidden
from backend.moderation.models import ModerationAction, Report
from backend.moderation.schemas import (
    AccountRef,
    CaseDetail,
    CaseList,
    CaseSummary,
    DecideIn,
    Journal,
    JournalEntry,
    LookupIn,
    ReporterOut,
    ReportingIn,
    ReportOut,
    RoleIn,
    SuspendIn,
    Target,
    TeamAccount,
    TeamCharacter,
    TeamContent,
    TeamList,
    TeamMember,
    WhyIn,
)
from backend.servers.models import GameServer
from backend.stories.models import Story

router = APIRouter(prefix="/moderation", tags=["moderation"])

Moderator = Annotated[User, require(Capability.MODERATE)]
Banisher = Annotated[User, require(Capability.BAN)]
RoleKeeper = Annotated[User, require(Capability.MANAGE_ROLES)]

DURATIONS = {
    "day": timedelta(days=1),
    "week": timedelta(days=7),
    "month": timedelta(days=30),
    "forever": None,
}

TARGET_COLUMN = {
    "character": Report.target_character_id,
    "story": Report.target_story_id,
}


def log(
    session: Session,
    actor: User,
    action: str,
    reason: str,
    *,
    user_id: int | None = None,
    character_id: int | None = None,
    story_id: int | None = None,
    server_id: int | None = None,
    detail: str | None = None,
) -> None:
    session.add(
        ModerationAction(
            actor_id=actor.id,
            action=action,
            reason=reason.strip(),
            target_user_id=user_id,
            target_character_id=character_id,
            target_story_id=story_id,
            target_server_id=server_id,
            detail=detail,
        )
    )


def tell(
    background: BackgroundTasks,
    user: User | None,
    subject: str,
    body: str,
    *,
    contestable: bool = True,
) -> None:
    """Prévenir la personne concernée, après la réponse, comme tous les emails du site."""
    if user is None:
        return
    contact = f"{settings.site_url}/mentions-legales"
    footer = (
        "\n\nCette décision suit la charte de modération : "
        f"{settings.site_url}/moderation\n"
        f"Pour la contester, écris à l'adresse indiquée sur {contact} : "
        "un autre membre de l'équipe relira."
    )
    background.add_task(
        emails.send_email, user.email, subject, body + (footer if contestable else "")
    )


def check_rank(actor: User, target: User | None, *, npc_ok: bool = False) -> None:
    """On n'agit que sur un rang inférieur. Un PNJ n'a pas de joueur : il est aux admins."""
    if target is None:
        if npc_ok and can(actor, Capability.MANAGE_NPCS):
            return
        raise HTTPException(status_code=403, detail="Seul un admin agit sur un PNJ")
    if not outranks(actor, target):
        raise HTTPException(
            status_code=403,
            detail="On n'agit que sur un compte de rang inférieur au sien : passe la main.",
        )


# Les signaleurs, et ce qu'on a pensé de leurs signalements.


def reporter_stats(session: Session, ids: set[int]) -> dict[int, ReporterOut]:
    rows = session.execute(
        select(Report.reporter_id, Report.decision, func.count())
        .where(Report.reporter_id.in_(ids))
        .group_by(Report.reporter_id, Report.decision)
    ).all()
    stats: dict[int, Counter] = {i: Counter() for i in ids}
    for reporter_id, decision, count in rows:
        stats[reporter_id]["sent"] += count
        stats[reporter_id][decision or "open"] += count
    revoked = {
        u.id: u.report_banned_at is not None
        for u in session.scalars(select(User).where(User.id.in_(ids)))
    }
    return {
        i: ReporterOut(
            id=i,
            reports_sent=c["sent"],
            founded=c["founded"],
            abusive=c["abusive"],
            reporting_revoked=revoked.get(i, False),
        )
        for i, c in stats.items()
    }


GONE = ReporterOut(
    id=None, reports_sent=0, founded=0, abusive=0, reporting_revoked=False
)


def team_account(session: Session, user: User) -> TeamAccount:
    characters = session.scalars(
        select(Character)
        .where(Character.user_id == user.id)
        .options(selectinload(Character.server))
        .order_by(Character.position, Character.name)
    )
    return TeamAccount(
        id=user.id,
        role=user.role,
        created_at=user.created_at,
        verified=user.email_verified_at is not None,
        suspended=user.suspended(),
        banned_until=user.banned_until if user.suspended() else None,
        reporting_revoked=user.report_banned_at is not None,
        characters=[
            TeamCharacter(
                id=c.id,
                name=c.name,
                server=c.server.name if c.server else None,
                hidden=c.hidden_at is not None,
            )
            for c in characters
        ],
        reports_received=session.scalar(
            select(func.count()).where(Report.reported_user_id == user.id)
        )
        or 0,
        reports_sent=session.scalar(
            select(func.count()).where(Report.reporter_id == user.id)
        )
        or 0,
    )


# Les dossiers.


def content_of(
    session: Session, target: Target, target_id: int
) -> Character | Story | None:
    model = Character if target == "character" else Story
    return session.get(model, target_id)


def label_of(content: Character | Story | None, reports: list[Report]) -> str:
    if isinstance(content, Character):
        return content.name
    if isinstance(content, Story):
        return content.title
    # Disparu : on reprend ce que disait la dernière copie encore gardée.
    for report in reversed(reports):
        if report.snapshot:
            return report.snapshot.get("name") or report.snapshot.get("title") or "?"
    return "Contenu supprimé"


def summarize(
    target: Target,
    target_id: int,
    content: Character | Story | None,
    reports: list[Report],
    session: Session | None = None,
) -> CaseSummary:
    hidden = content is not None and content.hidden_at is not None
    return CaseSummary(
        target=target,
        target_id=target_id,
        label=label_of(content, reports),
        exists=content is not None,
        hidden=hidden,
        auto_hidden=hidden
        and session is not None
        and auto_hidden(session, target, target_id),
        open_reports=sum(1 for r in reports if r.handled_at is None),
        total_reports=len(reports),
        reasons=dict(Counter(r.reason for r in reports if r.handled_at is None)),
        last_reported_at=max(r.created_at for r in reports),
    )


def auto_hidden(session: Session, target: Target, target_id: int) -> bool:
    return was_auto_hidden(
        session,
        target_id if target == "character" else None,
        target_id if target == "story" else None,
    )


def on(target: Target, target_id: int) -> dict[str, int]:
    """La cible d'une ligne du journal, selon le genre de contenu."""
    return (
        {"character_id": target_id}
        if target == "character"
        else {"story_id": target_id}
    )


@router.get("/cases")
def list_cases(
    session: SessionDep,
    _: Moderator,
    status: Annotated[str, Query(pattern="^(open|closed)$")] = "open",
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> CaseList:
    """Les dossiers ouverts d'abord : les plus signalés, puis les plus récents."""
    cases: dict[tuple[Target, int], list[Report]] = {}
    for report in session.scalars(select(Report).order_by(Report.created_at)):
        if report.target_character_id is not None:
            key: tuple[Target, int] = ("character", report.target_character_id)
        elif report.target_story_id is not None:
            key = ("story", report.target_story_id)
        else:
            continue
        cases.setdefault(key, []).append(report)

    summaries = [
        summarize(
            target, target_id, content_of(session, target, target_id), reports, session
        )
        for (target, target_id), reports in cases.items()
    ]
    if status == "open":
        summaries = [s for s in summaries if s.open_reports > 0]
        # Masqués automatiquement d'abord : un contenu attend, caché, qu'on le regarde.
        summaries.sort(
            key=lambda s: (s.auto_hidden, s.open_reports, s.last_reported_at),
            reverse=True,
        )
    else:
        summaries = [s for s in summaries if s.open_reports == 0]
        summaries.sort(key=lambda s: s.last_reported_at, reverse=True)
    return CaseList(items=summaries[offset : offset + limit], total=len(summaries))


def case_reports(session: Session, target: Target, target_id: int) -> list[Report]:
    return list(
        session.scalars(
            select(Report)
            .where(TARGET_COLUMN[target] == target_id)
            .order_by(Report.created_at)
        )
    )


@router.get("/cases/{target}/{target_id}")
def read_case(
    target: Target, target_id: int, session: SessionDep, _: Moderator
) -> CaseDetail:
    reports = case_reports(session, target, target_id)
    if not reports:
        raise HTTPException(status_code=404, detail="Aucun signalement pour ce contenu")
    content = content_of(session, target, target_id)
    owner_id = content.user_id if content is not None else reports[-1].reported_user_id
    owner = session.get(User, owner_id) if owner_id else None
    stats = reporter_stats(session, {r.reporter_id for r in reports if r.reporter_id})
    return CaseDetail(
        **summarize(target, target_id, content, reports, session).model_dump(),
        owner=team_account(session, owner) if owner else None,
        reports=[
            ReportOut(
                id=r.id,
                reason=r.reason,
                details=r.details,
                created_at=r.created_at,
                decision=r.decision,
                handled_at=r.handled_at,
                reporter=stats.get(r.reporter_id, GONE) if r.reporter_id else GONE,
                snapshot=r.snapshot,
            )
            for r in reports
        ],
    )


@router.post("/cases/{target}/{target_id}/decide")
def decide(
    target: Target,
    target_id: int,
    data: DecideIn,
    session: SessionDep,
    actor: Moderator,
    background: BackgroundTasks,
) -> CaseDetail:
    """Trancher les signalements en attente d'un contenu. Leurs copies sont alors effacées."""
    pending = [
        r for r in case_reports(session, target, target_id) if r.handled_at is None
    ]
    if not pending:
        raise HTTPException(
            status_code=409, detail="Ce dossier n'a plus rien en attente"
        )
    content = content_of(session, target, target_id)
    # Masqué automatiquement, et finalement rien à reprocher : rétabli dans la foulée.
    restore = (
        data.decision in ("no_action", "abusive")
        and content is not None
        and content.hidden_at is not None
        and auto_hidden(session, target, target_id)
    )
    now = datetime.now(UTC)
    for report in pending:
        report.decision = data.decision
        report.handled_by = actor.id
        report.handled_at = now
        report.snapshot = None
    log(
        session,
        actor,
        "decide",
        data.reason,
        user_id=pending[-1].reported_user_id,
        detail=data.decision,
        **on(target, target_id),
    )
    if restore and content is not None:
        content.hidden_at = None
        log(
            session,
            actor,
            "unhide",
            data.reason,
            user_id=content.user_id,
            **on(target, target_id),
        )
        owner = session.get(User, content.user_id) if content.user_id else None
        name = content.name if isinstance(content, Character) else content.title
        what = "Ta fiche" if target == "character" else "Ton histoire"
        tell(
            background,
            owner,
            f"{what} « {name} » est de nouveau visible",
            "Un modérateur a regardé les signalements : rien à reprocher à "
            f"{what.lower()} « {name} », de nouveau visible de tous.",
            contestable=False,
        )
    session.commit()
    return read_case(target, target_id, session, actor)


def team_content(session: Session, target: Target, target_id: int) -> TeamContent:
    content = content_of(session, target, target_id)
    if content is None:
        raise HTTPException(status_code=404, detail="Contenu introuvable")
    owner = session.get(User, content.user_id) if content.user_id else None
    return TeamContent(
        target=target,
        target_id=target_id,
        hidden=content.hidden_at is not None,
        owner=team_account(session, owner) if owner else None,
        open_reports=session.scalar(
            select(func.count()).where(
                TARGET_COLUMN[target] == target_id, Report.handled_at.is_(None)
            )
        )
        or 0,
    )


@router.get("/characters/{target_id}")
def read_character_for_team(
    target_id: int, session: SessionDep, _: Moderator
) -> TeamContent:
    return team_content(session, "character", target_id)


@router.get("/stories/{target_id}")
def read_story_for_team(
    target_id: int, session: SessionDep, _: Moderator
) -> TeamContent:
    return team_content(session, "story", target_id)


# Masquer, rétablir.


def set_hidden(
    target: Target,
    target_id: int,
    hidden: bool,
    data: WhyIn,
    session: Session,
    actor: User,
    background: BackgroundTasks,
) -> dict[str, str]:
    content = content_of(session, target, target_id)
    if content is None:
        raise HTTPException(status_code=404, detail="Contenu introuvable")
    owner = session.get(User, content.user_id) if content.user_id else None
    check_rank(actor, owner, npc_ok=True)
    if (content.hidden_at is not None) == hidden:
        raise HTTPException(
            status_code=409,
            detail="C'est déjà masqué" if hidden else "Ce n'est pas masqué",
        )
    content.hidden_at = datetime.now(UTC) if hidden else None
    what = "Ta fiche" if target == "character" else "Ton histoire"
    name = content.name if isinstance(content, Character) else content.title
    log(
        session,
        actor,
        "hide" if hidden else "unhide",
        data.reason,
        user_id=content.user_id,
        **(
            {"character_id": content.id}
            if target == "character"
            else {"story_id": content.id}
        ),
    )
    session.commit()
    if hidden:
        tell(
            background,
            owner,
            f"{what} « {name} » a été masquée",
            f"{what} « {name} » n'est plus visible des autres membres. Toi, tu la vois "
            f"toujours, et tu peux la modifier.\n\nLa raison : {data.reason.strip()}",
        )
    else:
        tell(
            background,
            owner,
            f"{what} « {name} » est de nouveau visible",
            f"{what} « {name} » est de nouveau visible de tous.\n\n"
            f"Le mot de l'équipe : {data.reason.strip()}",
        )
    return {"detail": "Masqué." if hidden else "Rétabli."}


@router.post("/characters/{target_id}/hide")
def hide_character(
    target_id: int,
    data: WhyIn,
    session: SessionDep,
    actor: Moderator,
    background: BackgroundTasks,
) -> dict[str, str]:
    return set_hidden("character", target_id, True, data, session, actor, background)


@router.post("/characters/{target_id}/unhide")
def unhide_character(
    target_id: int,
    data: WhyIn,
    session: SessionDep,
    actor: Moderator,
    background: BackgroundTasks,
) -> dict[str, str]:
    return set_hidden("character", target_id, False, data, session, actor, background)


@router.post("/stories/{target_id}/hide")
def hide_story(
    target_id: int,
    data: WhyIn,
    session: SessionDep,
    actor: Moderator,
    background: BackgroundTasks,
) -> dict[str, str]:
    return set_hidden("story", target_id, True, data, session, actor, background)


@router.post("/stories/{target_id}/unhide")
def unhide_story(
    target_id: int,
    data: WhyIn,
    session: SessionDep,
    actor: Moderator,
    background: BackgroundTasks,
) -> dict[str, str]:
    return set_hidden("story", target_id, False, data, session, actor, background)


# Les comptes.


def load_account(session: Session, user_id: int) -> User:
    user = session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Compte introuvable")
    return user


@router.get("/accounts/{user_id}")
def read_account(user_id: int, session: SessionDep, _: Moderator) -> TeamAccount:
    return team_account(session, load_account(session, user_id))


@router.post("/accounts/{user_id}/suspend")
def suspend(
    user_id: int,
    data: SuspendIn,
    session: SessionDep,
    actor: Banisher,
    background: BackgroundTasks,
) -> TeamAccount:
    user = load_account(session, user_id)
    check_rank(actor, user)
    now = datetime.now(UTC)
    length = DURATIONS[data.duration]
    user.banned_at = now
    user.banned_until = now + length if length else None
    # Les connexions en cours s'arrêtent tout de suite.
    session.execute(delete(UserSession).where(UserSession.user_id == user.id))
    log(session, actor, "suspend", data.reason, user_id=user.id, detail=data.duration)
    session.commit()
    until = (
        f"jusqu'au {user.banned_until.astimezone(PARIS):%d/%m/%Y à %H:%M}"
        if user.banned_until
        else "sans date de fin"
    )
    tell(
        background,
        user,
        "Ton compte est suspendu",
        f"Ton compte est suspendu {until}. Tu ne peux plus te connecter d'ici là. "
        f"Tes personnages et tes histoires restent en ligne, sauf ceux que l'équipe "
        f"a masqués.\n\nLa raison : {data.reason.strip()}",
    )
    return team_account(session, user)


@router.post("/accounts/{user_id}/reinstate")
def reinstate(
    user_id: int,
    data: WhyIn,
    session: SessionDep,
    actor: Banisher,
    background: BackgroundTasks,
) -> TeamAccount:
    user = load_account(session, user_id)
    check_rank(actor, user)
    if not user.suspended():
        raise HTTPException(status_code=409, detail="Ce compte n'est pas suspendu")
    user.banned_at = None
    user.banned_until = None
    log(session, actor, "reinstate", data.reason, user_id=user.id)
    session.commit()
    tell(
        background,
        user,
        "Ton compte est rétabli",
        f"Ta suspension est levée : tu peux de nouveau te connecter.\n\n"
        f"Le mot de l'équipe : {data.reason.strip()}",
    )
    return team_account(session, user)


@router.post("/accounts/{user_id}/reporting")
def set_reporting(
    user_id: int,
    data: ReportingIn,
    session: SessionDep,
    actor: Moderator,
    background: BackgroundTasks,
) -> TeamAccount:
    """Retirer, ou rendre, le droit de signaler à qui en abuse."""
    user = load_account(session, user_id)
    check_rank(actor, user)
    if (user.report_banned_at is None) == data.allowed:
        raise HTTPException(status_code=409, detail="C'est déjà le cas")
    user.report_banned_at = None if data.allowed else datetime.now(UTC)
    log(
        session,
        actor,
        "restore_reporting" if data.allowed else "revoke_reporting",
        data.reason,
        user_id=user.id,
    )
    session.commit()
    if data.allowed:
        tell(
            background,
            user,
            "Tu peux de nouveau signaler",
            f"Ton droit de signaler un contenu t'est rendu.\n\n"
            f"Le mot de l'équipe : {data.reason.strip()}",
        )
    else:
        tell(
            background,
            user,
            "Tu ne peux plus signaler de contenu",
            "Plusieurs de tes signalements ont été jugés abusifs : le bouton « Signaler » "
            "t'est retiré. Ton compte, tes personnages et tes histoires ne changent pas. "
            "Si tu vois un jour quelque chose de grave, l'adresse de contact reste "
            f"ouverte.\n\nLa raison : {data.reason.strip()}",
        )
    return team_account(session, user)


# Les rôles (#81) : réservés aux admins.

ROLE_NAMES = {"user": "joueur", "moderator": "modérateur", "admin": "admin"}


@router.get("/team")
def list_team(session: SessionDep, _: Moderator) -> TeamList:
    """Les modérateurs et les admins, les admins d'abord."""
    members = session.scalars(
        select(User).where(User.role != Role.USER).order_by(User.role, User.id)
    ).all()
    names: dict[int, list[str]] = {m.id: [] for m in members}
    for character in session.scalars(
        select(Character)
        .where(Character.user_id.in_(names))
        .order_by(Character.position, Character.name)
    ):
        names[character.user_id].append(character.name)
    return TeamList(
        items=[
            TeamMember(
                id=m.id, role=m.role, characters=names[m.id], suspended=m.suspended()
            )
            for m in members
        ]
    )


@router.post("/accounts/lookup")
def lookup_account(data: LookupIn, session: SessionDep, _: RoleKeeper) -> AccountRef:
    """Retrouver un compte par son adresse exacte, pour lui donner un rôle. En POST : une
    adresse n'a rien à faire dans une URL, que les journaux du serveur gardent."""
    user = session.scalars(
        select(User).where(func.lower(User.email) == data.email.strip().lower())
    ).one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="Aucun compte avec cette adresse")
    return AccountRef(id=user.id)


@router.post("/accounts/{user_id}/role")
def change_role(
    user_id: int,
    data: RoleIn,
    session: SessionDep,
    actor: RoleKeeper,
    background: BackgroundTasks,
) -> TeamAccount:
    """Nommer ou retirer un modérateur ou un admin. Le dernier admin reste admin."""
    user = load_account(session, user_id)
    if user.role == data.role:
        raise HTTPException(status_code=409, detail="C'est déjà son rôle")
    before = user.role
    try:
        set_role(session, user, Role(data.role))
    except LastAdminError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    log(session, actor, "set_role", data.reason, user_id=user.id, detail=data.role)
    session.commit()
    tell(
        background,
        user,
        f"Tu es maintenant {ROLE_NAMES[data.role]} sur tRoolPlay",
        f"Ton rôle change : {ROLE_NAMES[before]} → {ROLE_NAMES[data.role]}.\n\n"
        f"Le mot de l'équipe : {data.reason.strip()}",
        contestable=False,
    )
    return team_account(session, user)


# Le journal (#82) : il se lit, il ne se modifie jamais.


@router.get("/journal")
def read_journal(
    session: SessionDep,
    _: Moderator,
    action: str | None = None,
    actor_id: int | None = None,
    target_user_id: int | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> Journal:
    query: Select = select(ModerationAction)
    if action:
        query = query.where(ModerationAction.action == action)
    if actor_id is not None:
        query = query.where(ModerationAction.actor_id == actor_id)
    if target_user_id is not None:
        query = query.where(ModerationAction.target_user_id == target_user_id)
    total = session.scalar(select(func.count()).select_from(query.subquery())) or 0
    entries = session.scalars(
        query.order_by(ModerationAction.created_at.desc(), ModerationAction.id.desc())
        .limit(limit)
        .offset(offset)
    )
    items = [JournalEntry.model_validate(e) for e in entries]
    server_ids = {e.target_server_id for e in items if e.target_server_id is not None}
    if server_ids:
        names = {
            server.id: server.name
            for server in session.scalars(
                select(GameServer).where(GameServer.id.in_(server_ids))
            )
        }
        for e in items:
            if e.target_server_id is not None:
                e.target_server_name = names.get(e.target_server_id)
    return Journal(items=items, total=total)
