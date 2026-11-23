from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, computed_field

from backend.characters.classes import CharacterClass
from backend.servers.schemas import ServerOut

Period = Literal["morning", "afternoon", "evening", "night"]


class HangoutOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    area: str
    x: int
    y: int
    label: str | None
    habits: str | None


class CharacterSummary(BaseModel):
    """Ce qu'une liste montre d'un personnage."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    server: ServerOut | None
    name: str
    gender: str
    class_: CharacterClass | None = Field(serialization_alias="class")
    level: int | None
    avatar: str | None
    seal: str | None
    hook: str | None
    play_days: list[int]
    play_periods: list[str]
    inactive_at: datetime | None = Field(exclude=True)

    @computed_field
    def inactive(self) -> bool:
        return self.inactive_at is not None


class CharacterOut(CharacterSummary):
    """La fiche complète, telle que tout le monde peut la lire."""

    is_npc: bool
    ingame_name: str | None
    appearance: str | None
    personality: str | None
    backstory: str | None
    goals: str | None
    flaws: str | None
    rumors: str | None
    ooc_note: str | None
    hangouts: list[HangoutOut]
    inactive_note: str | None
    created_at: datetime
    updated_at: datetime


class CharacterList(BaseModel):
    items: list[CharacterSummary]
    total: int
