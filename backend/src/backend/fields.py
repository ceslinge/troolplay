"""Les types de champs partagés par toute l'API."""

from typing import Annotated

from pydantic import StringConstraints


def filled(min_length: int, max_length: int):
    """Un texte qui exige un contenu : les espaces autour sont retirés avant de compter.

    « ␣␣␣ » n'est ni un nom, ni un titre, ni une raison (tests/test_text_fields.py).
    """
    return Annotated[
        str,
        StringConstraints(
            strip_whitespace=True, min_length=min_length, max_length=max_length
        ),
    ]
