"""Limiter une action répétée : au-delà, 429 avec le délai d'attente."""

from datetime import UTC, datetime, timedelta

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.accounts.models import ThrottleEvent


def throttle(
    session: Session, action: str, key: str, limit: int, window: timedelta
) -> None:
    """Compte l'action, ou refuse si la limite est atteinte sur la période."""
    since = datetime.now(UTC) - window
    count = session.scalar(
        select(func.count()).where(
            ThrottleEvent.action == action,
            ThrottleEvent.key == key,
            ThrottleEvent.created_at > since,
        )
    )
    if count is not None and count >= limit:
        raise HTTPException(
            status_code=429,
            detail="Trop de demandes. Réessaie un peu plus tard.",
            headers={"Retry-After": str(int(window.total_seconds()))},
        )
    session.add(ThrottleEvent(action=action, key=key))
    session.flush()
