"""Les gestes d'équipe en ligne de commande, pour ne jamais ouvrir la base à la main.

uv run python -m backend.admin promote <adresse> --role admin
uv run python -m backend.admin team
"""

import argparse
import sys

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.accounts.models import User
from backend.accounts.roles import LastAdminError, Role, set_role
from backend.db import SessionLocal


def promote(session: Session, email: str, role: Role) -> str:
    """Donne ce rôle au compte. Renvoie ce qui a changé, ou lève une erreur à afficher."""
    user = session.scalars(
        select(User).where(func.lower(User.email) == email.strip().lower())
    ).one_or_none()
    if user is None:
        raise LookupError(f"Aucun compte avec l'adresse {email}.")
    before = user.role
    set_role(session, user, role)
    if before == role:
        return f"{user.email} est déjà {role}."
    return f"{user.email} : {before} → {role}."


def team(session: Session) -> list[str]:
    """Les modérateurs et les admins, les admins d'abord."""
    members = session.scalars(
        select(User)
        .where(User.role != Role.USER)
        .order_by(User.role, func.lower(User.email))
    ).all()
    return [
        f"{user.role:<10} {user.email}{'  (banni)' if user.banned_at else ''}"
        for user in members
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m backend.admin")
    commands = parser.add_subparsers(dest="command", required=True)
    promote_parser = commands.add_parser("promote", help="donner un rôle à un compte")
    promote_parser.add_argument("email")
    promote_parser.add_argument(
        "--role", required=True, choices=[role.value for role in Role]
    )
    commands.add_parser("team", help="lister les modérateurs et les admins")
    args = parser.parse_args(argv)

    with SessionLocal.begin() as session:
        if args.command == "team":
            print("\n".join(team(session)) or "Personne dans l'équipe pour l'instant.")
            return 0
        try:
            print(promote(session, args.email, Role(args.role)))
        except (LookupError, LastAdminError) as error:
            print(error, file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
