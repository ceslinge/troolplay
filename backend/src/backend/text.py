"""Petits outils de français pour ce que le backend écrit lui-même."""

import re

VOWEL = re.compile(r"[aeiouàâäéèêëîïôöùûüœæ]", re.IGNORECASE)


def of_name(name: str) -> str:
    """« de Gorrik », « d’Ombre », « d’Ysolde » : élidé devant une voyelle.

    Le Y s’élide quand il sonne comme une voyelle (Ysolde, Yves), pas devant une autre
    voyelle (Yugo). Le H reste tel quel. Même règle côté site : frontend/src/lib/text.ts.
    """
    elided = bool(VOWEL.match(name)) or (
        name[:1].lower() == "y" and not VOWEL.match(name[1:])
    )
    return f"d’{name}" if elided else f"de {name}"
