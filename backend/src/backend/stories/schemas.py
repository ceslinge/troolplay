from datetime import datetime
from typing import Annotated, Literal

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    computed_field,
)

from backend.characters.classes import CharacterClass
from backend.characters.schemas import no_duplicates
from backend.servers.schemas import ServerOut

Warning = Literal[
    "violence",
    "death",
    "torture",
    "sexual_themes",
    "abuse",
    "self_harm",
    "addiction",
    "phobia",
]

# Les règles des champs, écrites une fois (docs/api.md, « Champs et limites »).
Title = Annotated[str, Field(min_length=1, max_length=120)]
Body = Annotated[str, Field(max_length=50_000)]
Warnings = Annotated[list[Warning], AfterValidator(no_duplicates)]
Note = Annotated[str | None, Field(max_length=200)]
AuthorNote = Annotated[str | None, Field(max_length=1000)]

EXCERPT_LENGTH = 200


class StoryCharacter(BaseModel):
    """Le personnage qui signe, tel qu'une histoire le présente."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    gender: str
    class_: CharacterClass | None = Field(serialization_alias="class")
    avatar: str | None
    seal: str | None
    server: ServerOut | None


class StoryFields(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: Title | None = None
    body: Body | None = None
    content_warnings: Warnings | None = None
    content_note: Note = None
    author_note: AuthorNote = None


class StoryCreate(StoryFields):
    character_id: int
    title: Title
    body: Body = ""
    content_warnings: Warnings = []


class StoryUpdate(StoryFields):
    character_id: int | None = None


class StorySummary(BaseModel):
    """Ce qu'une liste montre d'une histoire."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    character: StoryCharacter | None
    content_warnings: list[str]
    content_note: str | None
    published_at: datetime | None
    body: str = Field(exclude=True)

    @computed_field
    def excerpt(self) -> str | None:
        # Une histoire avertie ne se dévoile pas avant qu'on choisisse de la lire.
        if self.content_warnings:
            return None
        text = " ".join(self.body.split())
        if len(text) <= EXCERPT_LENGTH:
            return text
        return text[:EXCERPT_LENGTH].rsplit(" ", 1)[0] + "…"


class StoryList(BaseModel):
    items: list[StorySummary]
    total: int


class MyStorySummary(StorySummary):
    """Le résumé, tel que son auteur le voit : brouillons et masquage compris."""

    updated_at: datetime
    hidden_at: datetime | None = Field(exclude=True)

    @computed_field
    def published(self) -> bool:
        return self.published_at is not None

    @computed_field
    def hidden(self) -> bool:
        return self.hidden_at is not None


class MyStories(BaseModel):
    items: list[MyStorySummary]


class StoryOut(BaseModel):
    """L'histoire complète."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    body: str
    character: StoryCharacter | None
    content_warnings: list[str]
    content_note: str | None
    author_note: str | None
    published_at: datetime | None
    updated_at: datetime
    is_mine: bool = False

    @computed_field
    def published(self) -> bool:
        return self.published_at is not None


class StoryOwnedOut(StoryOut):
    """Pour son auteur et la modération : on sait aussi si elle est masquée."""

    hidden_at: datetime | None = Field(exclude=True)

    @computed_field
    def hidden(self) -> bool:
        return self.hidden_at is not None
