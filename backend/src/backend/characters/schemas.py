from datetime import datetime
from typing import Annotated, Literal

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    computed_field,
    model_validator,
)

from backend.characters.classes import CharacterClass
from backend.fields import filled
from backend.servers.schemas import ServerOut

Period = Literal["morning", "afternoon", "evening", "night"]
Gender = Literal["feminine", "masculine", "neutral"]


def no_duplicates(values: list) -> list:
    if len(set(values)) != len(values):
        raise ValueError("Chaque valeur ne peut apparaître qu'une fois")
    return values


# Les règles des champs, écrites une fois (docs/api.md, « Champs et limites »).
Name = filled(2, 40)
Day = Annotated[int, Field(ge=1, le=7)]
Days = Annotated[list[Day], AfterValidator(no_duplicates)]
Periods = Annotated[list[Period], AfterValidator(no_duplicates)]


def text(max_length: int):
    return Annotated[str | None, Field(max_length=max_length)]


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
    # Vrai seulement pour la personne qui l'ignore : personne d'autre ne le sait (#112).
    ignored: bool = False


class CharacterList(BaseModel):
    items: list[CharacterSummary]
    total: int


class CharacterOwnedSummary(CharacterSummary):
    """Le résumé, tel que son propriétaire le voit."""

    hidden_at: datetime | None = Field(exclude=True)

    @computed_field
    def hidden(self) -> bool:
        return self.hidden_at is not None

    # Vrai pour le propriétaire. Un modérateur voit aussi « hidden », mais pas « is_mine ».
    is_mine: bool = True


class CharacterOwnedOut(CharacterOut, CharacterOwnedSummary):
    """La fiche complète, telle que son propriétaire la voit."""


class MyCharacters(BaseModel):
    items: list[CharacterOwnedSummary]


class CharacterOrder(BaseModel):
    """Tous ses personnages, dans l'ordre voulu."""

    model_config = ConfigDict(extra="forbid")

    ids: Annotated[list[int], AfterValidator(no_duplicates)]


class CharacterFields(BaseModel):
    """Les champs qu'on peut écrire, tous facultatifs."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    gender: Gender | None = None
    ingame_name: text(40) = None
    class_: CharacterClass | None = Field(default=None, alias="class")
    level: Annotated[int | None, Field(ge=1)] = None
    avatar: text(40) = None
    seal: text(40) = None
    hook: text(200) = None
    appearance: text(2000) = None
    personality: text(2000) = None
    backstory: text(10000) = None
    goals: text(2000) = None
    flaws: text(2000) = None
    rumors: text(2000) = None
    ooc_note: text(500) = None
    play_days: Days | None = None
    play_periods: Periods | None = None


class CharacterCreate(CharacterFields):
    name: Name
    server_id: int | None = None
    is_npc: bool = False

    @model_validator(mode="after")
    def npc_has_no_server(self) -> "CharacterCreate":
        # Un PNJ n'appartient à personne ni à aucun serveur (décision 5).
        if self.is_npc and self.server_id is not None:
            raise ValueError("Un PNJ n'a pas de serveur")
        if not self.is_npc and self.server_id is None:
            raise ValueError("Il faut choisir un serveur")
        return self


class CharacterUpdate(CharacterFields):
    name: Name | None = None
    # Un personnage peut déménager (transfert, fusion, serveur temporaire fermé),
    # vers un serveur ouvert du même jeu (décision 29).
    server_id: int | None = None
    inactive: bool | None = None
    inactive_note: text(200) = None

    @model_validator(mode="after")
    def name_cannot_be_emptied(self) -> "CharacterUpdate":
        if "name" in self.model_fields_set and self.name is None:
            raise ValueError("Le nom ne peut pas être vidé")
        return self


class HangoutIn(BaseModel):
    """Un lieu de prédilection, tel qu'on l'envoie."""

    model_config = ConfigDict(extra="forbid")

    area: filled(1, 40)
    x: Annotated[int, Field(ge=-1000, le=1000)]
    y: Annotated[int, Field(ge=-1000, le=1000)]
    label: text(60) = None
    habits: text(200) = None


class Namesakes(BaseModel):
    """Ces noms sont-ils déjà portés sur le serveur ? Oui ou non, rien de plus (#122)."""

    name: bool
    ingame_name: bool
