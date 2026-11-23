from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, computed_field

from backend.characters.classes import CharacterClass
from backend.servers.schemas import ServerOut


class HangoutOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    area: str
    x: int
    y: int
    label: str | None
    habits: str | None


class CharacterOut(BaseModel):
    """La fiche complète, telle que tout le monde peut la lire."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    server: ServerOut | None
    is_npc: bool
    name: str
    gender: str
    ingame_name: str | None
    class_: CharacterClass | None = Field(serialization_alias="class")
    level: int | None
    avatar: str | None
    seal: str | None
    hook: str | None
    appearance: str | None
    personality: str | None
    backstory: str | None
    goals: str | None
    flaws: str | None
    rumors: str | None
    ooc_note: str | None
    play_days: list[int]
    play_periods: list[str]
    hangouts: list[HangoutOut]
    inactive_at: datetime | None = Field(exclude=True)
    inactive_note: str | None
    created_at: datetime
    updated_at: datetime

    @computed_field
    def inactive(self) -> bool:
        return self.inactive_at is not None
