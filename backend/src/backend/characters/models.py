from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    false,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.characters.classes import CLASS_VALUES_SQL
from backend.db import Base, Timestamps
from backend.servers.models import GameServer


class Character(Timestamps, Base):
    __tablename__ = "characters"
    __table_args__ = (
        CheckConstraint(
            "(is_npc AND user_id IS NULL AND server_id IS NULL)"
            " OR (NOT is_npc AND user_id IS NOT NULL AND server_id IS NOT NULL)",
            name="npc_owner",
        ),
        CheckConstraint("char_length(name) >= 2", name="name_length"),
        CheckConstraint(
            "gender IN ('feminine', 'masculine', 'neutral')", name="gender"
        ),
        CheckConstraint("level >= 1", name="level"),
        CheckConstraint(f"class IN ({CLASS_VALUES_SQL})", name="class"),
        CheckConstraint(
            "play_days <@ ARRAY[1, 2, 3, 4, 5, 6, 7]::smallint[]", name="play_days"
        ),
        CheckConstraint(
            "play_periods <@ ARRAY['morning', 'afternoon', 'evening', 'night']::varchar[]",
            name="play_periods",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    server_id: Mapped[int | None] = mapped_column(
        ForeignKey("game_servers.id", ondelete="RESTRICT"), index=True
    )
    is_npc: Mapped[bool] = mapped_column(server_default=false())
    name: Mapped[str] = mapped_column(String(40))
    gender: Mapped[str] = mapped_column(String(10), server_default="neutral")
    ingame_name: Mapped[str | None] = mapped_column(String(40))
    class_: Mapped[str | None] = mapped_column("class", String(20))
    level: Mapped[int | None]
    avatar: Mapped[str | None] = mapped_column(String(40))
    seal: Mapped[str | None] = mapped_column(String(40))
    hook: Mapped[str | None] = mapped_column(String(200))
    appearance: Mapped[str | None] = mapped_column(Text)
    personality: Mapped[str | None] = mapped_column(Text)
    backstory: Mapped[str | None] = mapped_column(Text)
    goals: Mapped[str | None] = mapped_column(Text)
    flaws: Mapped[str | None] = mapped_column(Text)
    rumors: Mapped[str | None] = mapped_column(Text)
    ooc_note: Mapped[str | None] = mapped_column(Text)
    play_days: Mapped[list[int]] = mapped_column(
        ARRAY(SmallInteger), server_default=text("'{}'")
    )
    play_periods: Mapped[list[str]] = mapped_column(
        ARRAY(String(10)), server_default=text("'{}'")
    )
    inactive_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    inactive_note: Mapped[str | None] = mapped_column(String(200))
    hidden_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # La place du personnage dans la barre de son joueur, choisie par lui.
    position: Mapped[int] = mapped_column(SmallInteger, server_default="0")

    server: Mapped[GameServer | None] = relationship()
    hangouts: Mapped[list["CharacterHangout"]] = relationship(
        order_by="CharacterHangout.id", passive_deletes=True
    )


class CharacterHangout(Base):
    __tablename__ = "character_hangouts"
    __table_args__ = (UniqueConstraint("character_id", "area", "x", "y"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    character_id: Mapped[int] = mapped_column(
        ForeignKey("characters.id", ondelete="CASCADE"), index=True
    )
    area: Mapped[str] = mapped_column(String(40))
    x: Mapped[int]
    y: Mapped[int]
    label: Mapped[str | None] = mapped_column(String(60))
    habits: Mapped[str | None] = mapped_column(String(200))
