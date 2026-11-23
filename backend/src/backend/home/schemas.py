from pydantic import BaseModel

from backend.characters.schemas import CharacterSummary, Period
from backend.servers.schemas import ServerOut


class RightNow(BaseModel):
    """Qui a l'habitude d'être là à cette heure-ci, d'après les horaires déclarés."""

    server: ServerOut
    day: int
    period: Period
    count: int
    places: list[str]


class Overheard(BaseModel):
    """Une réplique d'accroche, tirée au hasard."""

    character_id: int
    name: str
    server: str | None
    hook: str


class HomeOut(BaseModel):
    right_now: RightNow | None
    overheard: Overheard | None
    recent: list[CharacterSummary]
