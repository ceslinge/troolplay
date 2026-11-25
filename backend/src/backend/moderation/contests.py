"""Contester une décision depuis le site (#141).

Une personne voit les décisions qui la visent et peut contester chacune une seule fois,
même suspendue : ce sont les seules routes, avec /me et la déconnexion, ouvertes à un
compte suspendu (SessionUser ; tests/test_suspended.py en tient la liste).
L'équipe répond une fois : décision maintenue, ou levée, et le site lève alors la mesure.
"""

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.accounts.models import User
from backend.accounts.sessions import SessionUser
from backend.characters.models import Character
from backend.db import SessionDep
from backend.moderation.models import CONTESTABLE, Contest, ModerationAction
from backend.moderation.schemas import (
    AnswerIn,
    ContestIn,
    ContestOut,
    JournalEntry,
    MyDecision,
    MyDecisions,
    TeamContest,
    TeamContests,
)
from backend.moderation.team import Moderator, check_rank, log, tell
from backend.stories.models import Story

me_router = APIRouter(prefix="/me/decisions", tags=["moderation"])
router = APIRouter(prefix="/moderation/contests", tags=["moderation"])

OUTCOME_WORDS = {"upheld": "est maintenue", "lifted": "est levée"}


def target_name(session: Session, action: ModerationAction) -> str | None:
    if action.target_character_id is not None:
        character = session.get(Character, action.target_character_id)
        return character.name if character else None
    if action.target_story_id is not None:
        story = session.get(Story, action.target_story_id)
        return story.title if story else None
    return None


def contest_of(session: Session, action_id: int) -> Contest | None:
    return session.scalars(
        select(Contest).where(Contest.action_id == action_id)
    ).one_or_none()


def my_decision(session: Session, action: ModerationAction) -> MyDecision:
    contest = contest_of(session, action.id)
    return MyDecision(
        id=action.id,
        action=action.action,
        detail=action.detail,
        reason=action.reason,
        created_at=action.created_at,
        target_character_id=action.target_character_id,
        target_story_id=action.target_story_id,
        target_name=target_name(session, action),
        contest=ContestOut.model_validate(contest) if contest else None,
    )


def load_my_decision(session: Session, action_id: int, user: User) -> ModerationAction:
    action = session.get(ModerationAction, action_id)
    if (
        action is None
        or action.target_user_id != user.id
        or action.action not in CONTESTABLE
    ):
        raise HTTPException(status_code=404, detail="Décision introuvable")
    return action


@me_router.get("")
def list_my_decisions(user: SessionUser, session: SessionDep) -> MyDecisions:
    """Les décisions qui me visent, les plus récentes d'abord."""
    actions = session.scalars(
        select(ModerationAction)
        .where(
            ModerationAction.target_user_id == user.id,
            ModerationAction.action.in_(CONTESTABLE),
        )
        .order_by(ModerationAction.created_at.desc(), ModerationAction.id.desc())
    )
    return MyDecisions(items=[my_decision(session, a) for a in actions])


@me_router.post("/{action_id}/contest", status_code=201)
def contest_decision(
    action_id: int, data: ContestIn, user: SessionUser, session: SessionDep
) -> MyDecision:
    action = load_my_decision(session, action_id, user)
    if contest_of(session, action.id) is not None:
        raise HTTPException(
            status_code=409, detail="Tu as déjà contesté cette décision"
        )
    session.add(Contest(action_id=action.id, user_id=user.id, body=data.body))
    try:
        session.commit()
    except IntegrityError as error:
        # Deux envois en même temps : la base n'en garde qu'un.
        session.rollback()
        raise HTTPException(
            status_code=409, detail="Tu as déjà contesté cette décision"
        ) from error
    return my_decision(session, action)


def team_contest(session: Session, contest: Contest, viewer: User) -> TeamContest:
    action = session.get(ModerationAction, contest.action_id)
    return TeamContest(
        id=contest.id,
        body=contest.body,
        created_at=contest.created_at,
        answer=contest.answer,
        outcome=contest.outcome,
        answered_at=contest.answered_at,
        contester_id=contest.user_id,
        decision=JournalEntry.model_validate(action),
        target_name=target_name(session, action),
        decided_by_me=action.actor_id == viewer.id,
    )


@router.get("")
def list_contests(
    session: SessionDep,
    viewer: Moderator,
    status: Annotated[str, Query(pattern="^(open|answered)$")] = "open",
) -> TeamContests:
    """Les contestations en attente (les plus anciennes d'abord), ou traitées."""
    open_ = status == "open"
    query = select(Contest).where(
        Contest.answered_at.is_(None) if open_ else Contest.answered_at.is_not(None)
    )
    total = session.scalar(select(func.count()).select_from(query.subquery())) or 0
    contests = session.scalars(
        query.order_by(
            Contest.created_at.asc() if open_ else Contest.answered_at.desc()
        ).limit(100)
    )
    return TeamContests(
        items=[team_contest(session, c, viewer) for c in contests], total=total
    )


def lift(session: Session, actor: User, action: ModerationAction, reason: str) -> None:
    """Lever la mesure, si elle tient encore, par le même geste qu'à la main, au journal."""
    owner = session.get(User, action.target_user_id) if action.target_user_id else None
    if action.action in ("hide", "auto_hide"):
        content = None
        if action.target_character_id is not None:
            content = session.get(Character, action.target_character_id)
        elif action.target_story_id is not None:
            content = session.get(Story, action.target_story_id)
        if content is None or content.hidden_at is None:
            return
        content.hidden_at = None
        log(
            session,
            actor,
            "unhide",
            reason,
            user_id=action.target_user_id,
            character_id=action.target_character_id,
            story_id=action.target_story_id,
        )
        return
    if owner is None:
        return
    if action.action == "suspend" and owner.suspended():
        owner.banned_at = None
        owner.banned_until = None
        log(session, actor, "reinstate", reason, user_id=owner.id)
    elif action.action == "revoke_reporting" and owner.report_banned_at is not None:
        owner.report_banned_at = None
        log(session, actor, "restore_reporting", reason, user_id=owner.id)


@router.post("/{contest_id}/answer")
def answer_contest(
    contest_id: int,
    data: AnswerIn,
    session: SessionDep,
    actor: Moderator,
    background: BackgroundTasks,
) -> TeamContest:
    contest = session.get(Contest, contest_id)
    if contest is None:
        raise HTTPException(status_code=404, detail="Contestation introuvable")
    if contest.answered_at is not None:
        raise HTTPException(
            status_code=409, detail="Cette contestation a déjà sa réponse"
        )
    contester = session.get(User, contest.user_id) if contest.user_id else None
    # Un compte effacé depuis n'a plus personne à protéger d'un rang à l'autre.
    if contester is not None:
        check_rank(actor, contester)
    action = session.get(ModerationAction, contest.action_id)
    contest.answer = data.answer
    contest.outcome = data.outcome
    contest.answered_by = actor.id
    contest.answered_at = datetime.now(UTC)
    if data.outcome == "lifted":
        lift(session, actor, action, data.answer)
    log(
        session,
        actor,
        "answer_contest",
        data.answer,
        user_id=contest.user_id,
        detail=data.outcome,
    )
    session.commit()
    tell(
        background,
        contester,
        "L'équipe a relu ta contestation",
        f"La décision que tu as contestée {OUTCOME_WORDS[data.outcome]}.\n\n"
        f"Le mot de l'équipe : {data.answer}",
        contestable=False,
    )
    return team_contest(session, contest, actor)
