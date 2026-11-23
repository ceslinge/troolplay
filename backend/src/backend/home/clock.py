"""L'heure qu'il est, côté joueurs : à Paris, comme les créneaux des fiches."""

from datetime import datetime
from zoneinfo import ZoneInfo

PARIS = ZoneInfo("Europe/Paris")


def now_in_paris() -> datetime:
    """Isolée dans sa propre fonction pour que les tests puissent fixer l'heure."""
    return datetime.now(PARIS)


def period_of(moment: datetime) -> str:
    """Le créneau d'une heure : matin 6-12 h, après-midi 12-18 h, soir 18-24 h, nuit 0-6 h."""
    hour = moment.hour
    if 6 <= hour < 12:
        return "morning"
    if 12 <= hour < 18:
        return "afternoon"
    if hour >= 18:
        return "evening"
    return "night"
