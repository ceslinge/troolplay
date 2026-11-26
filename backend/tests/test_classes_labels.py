"""Les noms affichés des classes existent deux fois : ici, et pour le site. Ils doivent dire la même chose."""

import re
from pathlib import Path

from backend.characters.classes import CLASS_LABELS, CharacterClass

FRONTEND = (
    Path(__file__).resolve().parents[2] / "frontend" / "src" / "lib" / "classes.ts"
)


def test_every_class_has_a_name() -> None:
    assert set(CLASS_LABELS) == set(CharacterClass)


def test_the_site_says_the_same() -> None:
    site = dict(
        re.findall(r"^\s+(\w+): '([^']+)',$", FRONTEND.read_text(), re.MULTILINE)
    )

    assert site == {c.value: label for c, label in CLASS_LABELS.items()}
