"""Mots de passe et jetons : tout ce qui touche aux secrets des comptes."""

import hashlib
import secrets

from pwdlib import PasswordHash
from pwdlib.exceptions import UnknownHashError

_hasher = PasswordHash.recommended()  # Argon2id

# Un hash calculé une fois, pour vérifier « quelque chose » même quand le compte n'existe pas :
# la réponse prend alors autant de temps, et ne trahit pas les adresses inscrites.
_DUMMY_HASH = _hasher.hash("pas-un-vrai-mot-de-passe")


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str | None) -> bool:
    if password_hash is None:
        _hasher.verify(password, _DUMMY_HASH)
        return False
    try:
        return _hasher.verify(password, password_hash)
    except UnknownHashError:
        # Un compte sans vrai mot de passe (comme ceux de la démo) : connexion impossible.
        return False


def new_token() -> str:
    """Un jeton aléatoire de 32 octets, lisible dans un cookie ou un lien."""
    return secrets.token_urlsafe(32)


def token_hash(token: str) -> str:
    """Ce que la base garde d'un jeton : son empreinte, jamais le jeton lui-même."""
    return hashlib.sha256(token.encode()).hexdigest()
