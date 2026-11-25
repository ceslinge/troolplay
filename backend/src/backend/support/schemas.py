from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

from backend.fields import filled

Topic = Literal["question", "problem", "bug"]
Body = filled(10, 4000)


class ConversationIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    topic: Topic
    body: Body


class MessageIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    body: Body


class MessageOut(BaseModel):
    """Un message tel que le voit le membre : l'équipe parle d'une seule voix."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    from_team: bool
    body: str
    created_at: datetime


class ConversationOut(BaseModel):
    id: int
    topic: Topic
    created_at: datetime
    updated_at: datetime
    waiting_for_team: bool
    closed_at: datetime | None
    messages: list[MessageOut]


class Conversations(BaseModel):
    items: list[ConversationOut]


class TeamMessageOut(MessageOut):
    # L'équipe voit qui, en son sein, a répondu.
    author_id: int | None


class TeamConversationOut(ConversationOut):
    user_id: int
    messages: list[TeamMessageOut]


class TeamConversations(BaseModel):
    items: list[TeamConversationOut]
    total: int
