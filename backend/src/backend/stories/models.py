from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.characters.models import Character
from backend.db import Base

# Ce qui attend le lecteur : il choisit avant de lire (docs/api.md, « Les histoires »).
CONTENT_WARNINGS = (
    "violence",
    "death",
    "torture",
    "sexual_themes",
    "abuse",
    "self_harm",
    "addiction",
    "phobia",
)
_WARNINGS_SQL = ", ".join(f"'{w}'" for w in CONTENT_WARNINGS)


class Story(Base):
    """Une histoire : le compte la possède, un de ses personnages la signe.

    Elle part avec le compte, mais survit à son personnage : elle perd alors sa signature.
    """

    __tablename__ = "stories"
    __table_args__ = (
        CheckConstraint("char_length(title) >= 1", name="title_length"),
        CheckConstraint(
            f"content_warnings <@ ARRAY[{_WARNINGS_SQL}]::varchar[]",
            name="content_warnings",
        ),
        # Les listes de la communauté : publiées, les plus récentes d'abord.
        Index("ix_stories_published", "published_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    character_id: Mapped[int | None] = mapped_column(
        ForeignKey("characters.id", ondelete="SET NULL"), index=True
    )
    title: Mapped[str] = mapped_column(String(120))
    body: Mapped[str] = mapped_column(Text, server_default="")
    content_warnings: Mapped[list[str]] = mapped_column(
        ARRAY(String(20)), server_default=text("'{}'")
    )
    content_note: Mapped[str | None] = mapped_column(String(200))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    hidden_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    character: Mapped[Character | None] = relationship()
