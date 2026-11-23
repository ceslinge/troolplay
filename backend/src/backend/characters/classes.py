"""Les classes du jeu.

Ajouter une classe :
1. l'ajouter à CharacterClass, et aux jeux qui l'ont dans CLASSES_BY_GAME ;
2. ajouter son nom affiché dans frontend/src/lib/classes.ts
   (TypeScript refuse de compiler tant qu'il manque) ;
3. écrire une migration qui remplace la contrainte ck_characters_class,
   sur le modèle de « add bellaphone class ».
"""

from enum import StrEnum


class CharacterClass(StrEnum):
    """L'identifiant de chaque classe. Le nom affiché se trouve côté frontend."""

    FECA = "feca"
    OSAMODAS = "osamodas"
    ENUTROF = "enutrof"
    SRAM = "sram"
    XELOR = "xelor"
    ECAFLIP = "ecaflip"
    ENIRIPSA = "eniripsa"
    IOP = "iop"
    CRA = "cra"
    SADIDA = "sadida"
    SACRIEUR = "sacrieur"
    PANDAWA = "pandawa"
    ROUBLARD = "roublard"
    ZOBAL = "zobal"
    STEAMER = "steamer"
    ELIOTROPE = "eliotrope"
    HUPPERMAGE = "huppermage"
    OUGINAK = "ouginak"
    FORGELANCE = "forgelance"
    BELLAPHONE = "bellaphone"


C = CharacterClass

RETRO_CLASSES = frozenset(
    {C.FECA, C.OSAMODAS, C.ENUTROF, C.SRAM, C.XELOR, C.ECAFLIP}
    | {C.ENIRIPSA, C.IOP, C.CRA, C.SADIDA, C.SACRIEUR, C.PANDAWA}
)

CLASSES_BY_GAME: dict[str, frozenset[CharacterClass]] = {
    "dofus": frozenset(CharacterClass),
    "retro": RETRO_CLASSES,
    "touch": frozenset(CharacterClass)
    - {C.ELIOTROPE, C.HUPPERMAGE, C.OUGINAK, C.FORGELANCE},
}


def is_available(character_class: CharacterClass, game: str) -> bool:
    """La classe existe-t-elle dans ce jeu ?"""
    return character_class in CLASSES_BY_GAME[game]


CLASS_VALUES_SQL = ", ".join(f"'{c.value}'" for c in CharacterClass)
