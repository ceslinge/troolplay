"""Un garde-fou pour toute l'API : un champ texte qui exige un contenu n'accepte pas des espaces.

Un nom, un titre, une raison faits de seuls espaces passaient la validation (vu sur les
serveurs, #81, puis retrouvé ailleurs). Ce test passe en revue chaque modèle de l'API :
le prochain champ ajouté est vérifié d'office.
"""

import importlib
import pkgutil
from typing import Annotated

import pytest
from pydantic import BaseModel, TypeAdapter, ValidationError

import backend

# Un mot de passe est pris tel quel : des espaces y sont permis, rien ne doit les retirer.
EXEMPT = {"password", "new_password", "current_password"}


def all_models() -> list[type[BaseModel]]:
    for module in pkgutil.walk_packages(backend.__path__, "backend."):
        importlib.import_module(module.name)
    found: list[type[BaseModel]] = []
    pending = [BaseModel]
    while pending:
        for model in pending.pop().__subclasses__():
            pending.append(model)
            if model.__module__.startswith("backend."):
                found.append(model)
    return found


def min_length(metadata: list) -> int:
    return max((getattr(m, "min_length", None) or 0 for m in metadata), default=0)


TEXT_FIELDS = [
    pytest.param(model, name, field, id=f"{model.__name__}.{name}")
    for model in all_models()
    for name, field in model.model_fields.items()
    if name not in EXEMPT and min_length(field.metadata) > 0
]


def test_the_api_has_text_fields_to_check() -> None:
    assert len(TEXT_FIELDS) >= 5


@pytest.mark.parametrize(("model", "name", "field"), TEXT_FIELDS)
def test_spaces_are_not_content(model, name, field) -> None:
    adapter = TypeAdapter(Annotated[field.annotation, *field.metadata])
    blank = " " * max(min_length(field.metadata), 3)

    with pytest.raises(ValidationError):
        adapter.validate_python(blank)
