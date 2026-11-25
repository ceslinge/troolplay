"""Écrire à l'équipe (#142).

Un membre ouvre une conversation sur un sujet (question, problème, bug), l'équipe répond,
on peut continuer tant qu'elle est ouverte. L'équipe la clôt. Un compte suspendu n'y a
pas accès : il a la contestation (#141).
"""

from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session, selectinload

from backend.accounts import emails
from backend.accounts.models import User
from backend.accounts.sessions import CurrentUser
from backend.accounts.throttle import throttle
from backend.config import settings
from backend.db import SessionDep
from backend.moderation.team import Moderator
from backend.support.models import Conversation, SupportMessage
from backend.support.schemas import (
    ConversationIn,
    ConversationOut,
    Conversations,
    MessageIn,
    TeamConversationOut,
    TeamConversations,
)

me_router = APIRouter(prefix="/me/conversations", tags=["support"])
router = APIRouter(prefix="/moderation/conversations", tags=["support"])

# Contre le spam : quelques conversations ouvertes à la fois, et des messages comptés.
MAX_OPEN = 3
MESSAGE_LIMIT = 10
MESSAGE_WINDOW = timedelta(days=1)
# Une conversation close s'efface au bout d'un an (politique de confidentialité).
KEEP_CLOSED = timedelta(days=365)

WITH_MESSAGES = selectinload(Conversation.messages)


def purge(session: Session) -> None:
    """Efface les conversations closes depuis plus d'un an. Appelé en listant : pas de tâche planifiée."""
    session.execute(
        delete(Conversation).where(
            Conversation.closed_at < datetime.now(UTC) - KEEP_CLOSED
        )
    )


def add_message(
    session: Session, conversation: Conversation, author: User, body: str, team: bool
) -> None:
    now = datetime.now(UTC)
    session.add(
        SupportMessage(
            conversation_id=conversation.id,
            author_id=author.id,
            from_team=team,
            body=body,
            created_at=now,
        )
    )
    conversation.updated_at = now
    conversation.waiting_for_team = not team


def load_mine(session: Session, conversation_id: int, user: User) -> Conversation:
    conversation = session.get(Conversation, conversation_id)
    if conversation is None or conversation.user_id != user.id:
        raise HTTPException(status_code=404, detail="Conversation introuvable")
    return conversation


def mine_out(session: Session, conversation: Conversation) -> ConversationOut:
    session.refresh(conversation)
    return ConversationOut.model_validate(conversation, from_attributes=True)


@me_router.get("")
def list_my_conversations(user: CurrentUser, session: SessionDep) -> Conversations:
    purge(session)
    session.commit()
    conversations = session.scalars(
        select(Conversation)
        .where(Conversation.user_id == user.id)
        .options(WITH_MESSAGES)
        .order_by(Conversation.updated_at.desc())
    )
    return Conversations(
        items=[
            ConversationOut.model_validate(c, from_attributes=True)
            for c in conversations
        ]
    )


@me_router.post("", status_code=201)
def start_conversation(
    data: ConversationIn, user: CurrentUser, session: SessionDep
) -> ConversationOut:
    open_count = session.scalar(
        select(func.count()).where(
            Conversation.user_id == user.id, Conversation.closed_at.is_(None)
        )
    )
    if open_count is not None and open_count >= MAX_OPEN:
        raise HTTPException(
            status_code=409,
            detail=f"Tu as déjà {MAX_OPEN} demandes en cours : attends la réponse de l'équipe.",
        )
    throttle(
        session, "support", str(user.id), limit=MESSAGE_LIMIT, window=MESSAGE_WINDOW
    )
    conversation = Conversation(user_id=user.id, topic=data.topic)
    session.add(conversation)
    session.flush()
    add_message(session, conversation, user, data.body, team=False)
    session.commit()
    return mine_out(session, conversation)


@me_router.post("/{conversation_id}/messages", status_code=201)
def reply_as_member(
    conversation_id: int, data: MessageIn, user: CurrentUser, session: SessionDep
) -> ConversationOut:
    conversation = load_mine(session, conversation_id, user)
    if conversation.closed_at is not None:
        raise HTTPException(
            status_code=409, detail="Cette demande est close : ouvre-en une nouvelle."
        )
    throttle(
        session, "support", str(user.id), limit=MESSAGE_LIMIT, window=MESSAGE_WINDOW
    )
    add_message(session, conversation, user, data.body, team=False)
    session.commit()
    return mine_out(session, conversation)


def team_out(session: Session, conversation: Conversation) -> TeamConversationOut:
    session.refresh(conversation)
    return TeamConversationOut.model_validate(conversation, from_attributes=True)


def load_any(session: Session, conversation_id: int) -> Conversation:
    conversation = session.get(Conversation, conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation introuvable")
    return conversation


@router.get("")
def list_conversations(
    session: SessionDep,
    _: Moderator,
    status: Annotated[str, Query(pattern="^(waiting|answered|closed)$")] = "waiting",
) -> TeamConversations:
    """À répondre (les plus anciennes d'abord), en attente du membre, ou closes."""
    purge(session)
    session.commit()
    if status == "closed":
        query = select(Conversation).where(Conversation.closed_at.is_not(None))
        order = Conversation.closed_at.desc()
    else:
        query = select(Conversation).where(
            Conversation.closed_at.is_(None),
            Conversation.waiting_for_team.is_(status == "waiting"),
        )
        order = (
            Conversation.updated_at.asc()
            if status == "waiting"
            else Conversation.updated_at.desc()
        )
    total = session.scalar(select(func.count()).select_from(query.subquery())) or 0
    conversations = session.scalars(
        query.options(WITH_MESSAGES).order_by(order).limit(100)
    )
    return TeamConversations(
        items=[
            TeamConversationOut.model_validate(c, from_attributes=True)
            for c in conversations
        ],
        total=total,
    )


@router.post("/{conversation_id}/messages", status_code=201)
def reply_as_team(
    conversation_id: int,
    data: MessageIn,
    session: SessionDep,
    actor: Moderator,
    background: BackgroundTasks,
) -> TeamConversationOut:
    conversation = load_any(session, conversation_id)
    if conversation.closed_at is not None:
        raise HTTPException(status_code=409, detail="Cette conversation est close")
    add_message(session, conversation, actor, data.body, team=True)
    member = session.get(User, conversation.user_id)
    session.commit()
    # Le mail dit seulement qu'une réponse attend : le message reste sur le site.
    background.add_task(
        emails.send_email,
        member.email,
        "L'équipe t'a répondu",
        "L'équipe de tRoolPlay a répondu à ta demande. Tu peux la lire, et répondre, "
        f"depuis ton compte : {settings.site_url}/compte#demandes",
    )
    return team_out(session, conversation)


@router.post("/{conversation_id}/close")
def close_conversation(
    conversation_id: int, session: SessionDep, _: Moderator
) -> TeamConversationOut:
    conversation = load_any(session, conversation_id)
    if conversation.closed_at is not None:
        raise HTTPException(status_code=409, detail="Cette conversation est déjà close")
    conversation.closed_at = datetime.now(UTC)
    conversation.waiting_for_team = False
    session.commit()
    return team_out(session, conversation)
