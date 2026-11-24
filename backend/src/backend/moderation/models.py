from datetime import datetime
from typing import Any

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from backend.db import Base

# Les motifs suivent la charte de modération (docs/legal/moderation.md).
REASONS = (
    "off_topic",
    "disrespect",
    "hate",
    "explicit",
    "personal_info",
    "impersonation",
    "spam",
    "illegal",
    "other",
)
_REASONS_SQL = ", ".join(f"'{r}'" for r in REASONS)


class Report(Base):
    """Un signalement. Il survit à tout : à son auteur, au contenu visé, à son propriétaire.

    La copie du contenu (snapshot) garde ce qui a été signalé, même s'il change ou disparaît
    ensuite. Elle est effacée une fois le signalement traité (page de confidentialité).
    """

    __tablename__ = "reports"
    __table_args__ = (
        # Une cible au plus : un personnage ou une histoire. Les deux peuvent avoir disparu depuis.
        CheckConstraint(
            "target_character_id IS NULL OR target_story_id IS NULL", name="one_target"
        ),
        CheckConstraint(f"reason IN ({_REASONS_SQL})", name="reason"),
        CheckConstraint(
            "decision IS NULL OR decision IN ('founded', 'no_action', 'abusive')",
            name="decision",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    reporter_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    # Le propriétaire du contenu au moment du signalement : pour voir ce qui se répète.
    reported_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    target_character_id: Mapped[int | None] = mapped_column(
        ForeignKey("characters.id", ondelete="SET NULL"), index=True
    )
    target_story_id: Mapped[int | None] = mapped_column(
        ForeignKey("stories.id", ondelete="SET NULL"), index=True
    )
    reason: Mapped[str] = mapped_column(String(20))
    details: Mapped[str | None] = mapped_column(Text)
    snapshot: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    # Remplis par la modération (#51).
    decision: Mapped[str | None] = mapped_column(String(20))
    handled_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    handled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


# Ce que l'équipe peut faire : chaque action laisse une ligne au journal (#82).
ACTIONS = (
    "decide",
    "hide",
    "unhide",
    "suspend",
    "reinstate",
    "revoke_reporting",
    "restore_reporting",
    "set_role",
)
DECISIONS = ("founded", "no_action", "abusive")


class ModerationAction(Base):
    """Une ligne du journal de modération : qui, quoi, sur quoi, quand, pourquoi.

    Le site ne la modifie ni ne l'efface jamais. Elle survit à son auteur et à sa cible.
    """

    __tablename__ = "moderation_actions"
    __table_args__ = (
        CheckConstraint(
            "action IN (" + ", ".join(f"'{a}'" for a in ACTIONS) + ")", name="action"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    actor_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    action: Mapped[str] = mapped_column(String(20), index=True)
    target_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    target_character_id: Mapped[int | None] = mapped_column(
        ForeignKey("characters.id", ondelete="SET NULL")
    )
    target_story_id: Mapped[int | None] = mapped_column(
        ForeignKey("stories.id", ondelete="SET NULL")
    )
    # Une décision, une durée de suspension : ce que l'action a choisi.
    detail: Mapped[str | None] = mapped_column(String(20))
    reason: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
