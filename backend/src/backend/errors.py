"""Les erreurs que plusieurs routes renvoient de la même façon."""

from fastapi import HTTPException


def field_error(field: str, message: str) -> HTTPException:
    """Une erreur 422 sur un champ, dans le même format que celles de FastAPI."""
    return HTTPException(
        status_code=422,
        detail=[{"loc": ["body", field], "type": "value_error", "msg": message}],
    )
