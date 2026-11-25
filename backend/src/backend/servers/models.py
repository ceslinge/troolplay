from sqlalchemy import CheckConstraint, String, UniqueConstraint, true
from sqlalchemy.orm import Mapped, mapped_column

from backend.db import Base


class GameServer(Base):
    __tablename__ = "game_servers"
    __table_args__ = (
        UniqueConstraint("game", "name"),
        CheckConstraint("game IN ('dofus', 'retro', 'touch')", name="game"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    game: Mapped[str] = mapped_column(String(10))
    name: Mapped[str] = mapped_column(String(40))
    is_active: Mapped[bool] = mapped_column(server_default=true())
    # Son nom dans le catalogue (catalog.py), s'il en vient : renommé sur le site, il y reste reconnu.
    catalog_name: Mapped[str | None] = mapped_column(String(40))
