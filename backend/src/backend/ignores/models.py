from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.db import Base


class IgnoredCharacter(Base):
    """Un personnage qu'un membre ne veut plus croiser dans ses listes (#112).

    Privé : seul ce membre le sait. On ignore un personnage, jamais un joueur, pour ne
    rien révéler de qui joue quoi (décision 6).
    """

    __tablename__ = "ignored_characters"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    character_id: Mapped[int] = mapped_column(
        ForeignKey("characters.id", ondelete="CASCADE"), primary_key=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
