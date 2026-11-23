import pytest

from backend.characters.classes import CLASSES_BY_GAME, CharacterClass, is_available


def test_every_game_has_its_classes() -> None:
    assert set(CLASSES_BY_GAME) == {"dofus", "retro", "touch"}


def test_dofus_has_every_class() -> None:
    assert CLASSES_BY_GAME["dofus"] == frozenset(CharacterClass)


@pytest.mark.parametrize(
    ("character_class", "game", "expected"),
    [
        (CharacterClass.CRA, "retro", True),
        (CharacterClass.ROUBLARD, "retro", False),
        (CharacterClass.BELLAPHONE, "retro", False),
        (CharacterClass.ROUBLARD, "touch", True),
        (CharacterClass.HUPPERMAGE, "touch", False),
        (CharacterClass.BELLAPHONE, "touch", True),
        (CharacterClass.BELLAPHONE, "dofus", True),
    ],
)
def test_availability_depends_on_the_game(
    character_class: CharacterClass, game: str, expected: bool
) -> None:
    assert is_available(character_class, game) is expected
