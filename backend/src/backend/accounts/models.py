from datetime import UTC, datetime

from sqlalchemy import (
    CheckConstraint,
    ColumnElement,
    DateTime,
    ForeignKey,
    Index,
    String,
    and_,
    func,
    or_,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.db import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("role IN ('user', 'moderator', 'admin')", name="role"),
        Index("uq_users_email_lower", text("lower(email)"), unique=True),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(254))
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(10), server_default="user")
    email_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Suspendu depuis banned_at, jusqu'à banned_until ; sans fin, c'est un bannissement.
    banned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    banned_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Le droit de signaler, retiré par la modération à qui en abuse.
    report_banned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    def suspended(self, now: datetime | None = None) -> bool:
        """Suspendu en ce moment. Une suspension se lève toute seule à son terme."""
        if self.banned_at is None:
            return False
        return self.banned_until is None or self.banned_until > (
            now or datetime.now(UTC)
        )

    @staticmethod
    def active(now: datetime) -> ColumnElement[bool]:
        """La même règle, pour une requête : les comptes qui ne sont pas suspendus."""
        return or_(
            User.banned_at.is_(None),
            and_(User.banned_until.is_not(None), User.banned_until <= now),
        )


class UserSession(Base):
    """Une connexion ouverte. Le cookie porte le jeton, la base son empreinte."""

    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class LoginFailure(Base):
    """Une connexion ratée, gardée un temps pour limiter les essais."""

    __tablename__ = "login_failures"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(254), index=True)
    ip: Mapped[str] = mapped_column(String(45), index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )


class EmailToken(Base):
    """Un lien envoyé par email : vérifier son adresse, ou changer son mot de passe."""

    __tablename__ = "email_tokens"
    __table_args__ = (
        CheckConstraint("purpose IN ('verify', 'reset')", name="purpose"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    purpose: Mapped[str] = mapped_column(String(10))
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class ThrottleEvent(Base):
    """Une action limitée (inscription, renvoi d'email…), gardée pour la compter."""

    __tablename__ = "throttle_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    action: Mapped[str] = mapped_column(String(30))
    key: Mapped[str] = mapped_column(String(254))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
