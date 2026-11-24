"""Ce que chaque rôle peut faire, écrit une seule fois.

Les routes demandent une capacité, jamais un nom de rôle : donner un pouvoir de plus aux
modérateurs, c'est changer une ligne ici, relue dans une PR. Le site, lui, ne fait
qu'attribuer un rôle à quelqu'un.

Ce qui tient à la propriété (modifier sa fiche, la mettre en retrait, la supprimer) n'est
pas une capacité : ça dépend du personnage, pas du rôle.

Les modérateurs valent pour tout le site. S'ils deviennent un jour propres à un serveur,
c'est ici que la portée s'ajoutera, sans toucher aux routes qui demandent une capacité.
"""

from enum import StrEnum
from typing import Annotated

from fastapi import Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.accounts.models import User
from backend.accounts.sessions import current_user


class Role(StrEnum):
    USER = "user"
    MODERATOR = "moderator"
    ADMIN = "admin"


class Capability(StrEnum):
    SEE_HIDDEN = "see_hidden"
    """Lire un contenu masqué."""
    SEE_OWNER = "see_owner"
    """Savoir quel compte possède un personnage."""
    MODERATE = "moderate"
    """Masquer un contenu, traiter un signalement."""
    BAN = "ban"
    """Bannir un compte."""
    DELETE_ANY = "delete_any"
    """Supprimer le contenu d'un autre."""
    MANAGE_NPCS = "manage_npcs"
    """Créer, modifier et supprimer les PNJ."""
    MANAGE_SERVERS = "manage_servers"
    """Ajouter, fermer ou fusionner des serveurs."""
    MANAGE_ROLES = "manage_roles"
    """Nommer ou retirer modérateurs et admins."""


_MODERATION = frozenset(
    {Capability.SEE_HIDDEN, Capability.SEE_OWNER, Capability.MODERATE, Capability.BAN}
)

CAPABILITIES: dict[Role, frozenset[Capability]] = {
    Role.USER: frozenset(),
    Role.MODERATOR: _MODERATION,
    Role.ADMIN: frozenset(Capability),
}

# Du plus bas au plus haut : on n'agit que sur quelqu'un de rang inférieur.
RANK = {Role.USER: 0, Role.MODERATOR: 1, Role.ADMIN: 2}


def capabilities(user: User | None) -> frozenset[Capability]:
    """Ce que cette personne peut faire. Un visiteur ou un compte banni : rien."""
    if user is None or user.banned_at is not None:
        return frozenset()
    return CAPABILITIES[Role(user.role)]


def can(user: User | None, capability: Capability) -> bool:
    return capability in capabilities(user)


def outranks(actor: User, target: User) -> bool:
    """Bannir, masquer : seulement quelqu'un de rang inférieur au sien."""
    return RANK[Role(actor.role)] > RANK[Role(target.role)]


def require(capability: Capability):
    """Dépendance de route : la personne connectée, si elle a cette capacité, sinon 403."""

    def check(user: Annotated[User, Depends(current_user)]) -> User:
        if not can(user, capability):
            raise HTTPException(status_code=403, detail="Tu n'as pas ce droit")
        return user

    return Depends(check)


class LastAdminError(ValueError):
    pass


def set_role(session: Session, user: User, role: Role) -> None:
    """Change le rôle d'un compte. Le dernier admin ne peut pas être rétrogradé :
    le site ne doit jamais se retrouver sans personne aux commandes."""
    if user.role == Role.ADMIN and user.banned_at is None and role != Role.ADMIN:
        # Un admin banni ne tient plus les commandes : il ne compte pas.
        admins = session.scalar(
            select(func.count())
            .select_from(User)
            .where(User.role == Role.ADMIN, User.banned_at.is_(None))
        )
        if admins <= 1:
            raise LastAdminError(
                "C'est le dernier admin : nomme d'abord quelqu'un d'autre."
            )
    user.role = role
