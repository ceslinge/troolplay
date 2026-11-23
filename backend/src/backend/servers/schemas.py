from pydantic import BaseModel, ConfigDict, computed_field

from backend.characters.classes import CLASSES_BY_GAME, CharacterClass


class ServerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    game: str
    name: str

    @computed_field
    def classes(self) -> list[CharacterClass]:
        """Les classes qu'on peut jouer sur ce serveur, dans l'ordre du jeu."""
        available = CLASSES_BY_GAME[self.game]
        return [c for c in CharacterClass if c in available]


class ServerList(BaseModel):
    items: list[ServerOut]
