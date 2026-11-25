"""Écrire à l'équipe (#142) : une conversation entre un membre et l'équipe.

Les données d'une personne : elles partent avec son compte (CASCADE), et une
conversation close s'efface au bout d'un an (support/routes.py, purge).
"""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db import Base

TOPICS = ("question", "problem", "bug")


class Conversation(Base):
    __tablename__ = "conversations"
    __table_args__ = (
        CheckConstraint(
            "topic IN (" + ", ".join(f"'{t}'" for t in TOPICS) + ")", name="topic"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    topic: Mapped[str] = mapped_column(String(10))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    # Le dernier message, pour trier et savoir qui doit répondre.
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    waiting_for_team: Mapped[bool] = mapped_column(Boolean, default=True)
    closed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), index=True
    )
    messages: Mapped[list["SupportMessage"]] = relationship(
        order_by="SupportMessage.id", passive_deletes=True
    )


class SupportMessage(Base):
    __tablename__ = "support_messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    conversation_id: Mapped[int] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"), index=True
    )
    # Qui l'a écrit ; vide si son compte a été supprimé depuis.
    author_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    from_team: Mapped[bool] = mapped_column(Boolean)
    body: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
