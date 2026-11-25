from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, computed_field

from backend.characters.classes import CLASSES_BY_GAME, CharacterClass


class ServerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    game: str
    name: str
    is_active: bool = Field(exclude=True)

    @computed_field
    def closed(self) -> bool:
        """Un serveur fermé : ses fiches restent lisibles, on n'en crée plus."""
        return not self.is_active

    @computed_field
    def classes(self) -> list[CharacterClass]:
        """Les classes qu'on peut jouer sur ce serveur, dans l'ordre du jeu."""
        available = CLASSES_BY_GAME[self.game]
        return [c for c in CharacterClass if c in available]


class ServerList(BaseModel):
    items: list[ServerOut]


ServerName = Annotated[str, Field(min_length=2, max_length=40)]
Why = Annotated[str, Field(min_length=3, max_length=1000)]


class TeamServer(ServerOut):
    characters: int
    stories: int


class TeamServerList(BaseModel):
    items: list[TeamServer]


class ServerCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    game: Literal["dofus", "retro", "touch"]
    name: ServerName
    reason: Why


class ServerRename(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: ServerName
    reason: Why


class ServerWhy(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reason: Why
