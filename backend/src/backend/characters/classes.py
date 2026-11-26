"""Les classes du jeu.

Ajouter une classe :
1. l'ajouter à CharacterClass, et aux jeux qui l'ont dans CLASSES_BY_GAME ;
2. ajouter son nom affiché dans CLASS_LABELS ci-dessous et dans frontend/src/lib/classes.ts
   (TypeScript refuse de compiler tant qu'il manque ; tests/test_classes_labels.py vérifie
   que les deux listes disent la même chose) ;
3. écrire une migration qui remplace la contrainte ck_characters_class,
   sur le modèle de « add bellaphone class ».
"""

from enum import StrEnum


class CharacterClass(StrEnum):
    """L'identifiant de chaque classe. Le nom affiché est dans CLASS_LABELS."""

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


# Le nom affiché, pour ce que le backend écrit lui-même (les aperçus de liens, #53).
# Le site a la même liste, dans frontend/src/lib/classes.ts.
CLASS_LABELS: dict[CharacterClass, str] = {
    CharacterClass.FECA: "Féca",
    CharacterClass.OSAMODAS: "Osamodas",
    CharacterClass.ENUTROF: "Enutrof",
    CharacterClass.SRAM: "Sram",
    CharacterClass.XELOR: "Xélor",
    CharacterClass.ECAFLIP: "Ecaflip",
    CharacterClass.ENIRIPSA: "Eniripsa",
    CharacterClass.IOP: "Iop",
    CharacterClass.CRA: "Crâ",
    CharacterClass.SADIDA: "Sadida",
    CharacterClass.SACRIEUR: "Sacrieur",
    CharacterClass.PANDAWA: "Pandawa",
    CharacterClass.ROUBLARD: "Roublard",
    CharacterClass.ZOBAL: "Zobal",
    CharacterClass.STEAMER: "Steamer",
    CharacterClass.ELIOTROPE: "Eliotrope",
    CharacterClass.HUPPERMAGE: "Huppermage",
    CharacterClass.OUGINAK: "Ouginak",
    CharacterClass.FORGELANCE: "Forgelance",
    CharacterClass.BELLAPHONE: "Bellaphone",
}

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
