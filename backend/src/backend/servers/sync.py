"""Ajoute en base les serveurs du catalogue qui n'y sont pas encore. On peut le relancer sans risque."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.db import SessionLocal
from backend.servers.catalog import SERVERS
from backend.servers.models import GameServer


def sync(session: Session) -> list[tuple[str, str]]:
    """Les serveurs ajoutés. Ceux qui existent déjà, même fermés, ne sont pas touchés :
    un serveur fermé par l'équipe ne doit pas rouvrir tout seul."""
    known = {
        (game, name)
        for game, name in session.execute(select(GameServer.game, GameServer.name))
    }
    added = [
        (game, name)
        for game, names in SERVERS.items()
        for name in names
        if (game, name) not in known
    ]
    session.add_all(GameServer(game=game, name=name) for game, name in added)
    session.flush()
    return added


def main() -> None:
    with SessionLocal.begin() as session:
        added = sync(session)
    if added:
        print(f"{len(added)} serveur(s) ajouté(s) : {', '.join(n for _, n in added)}.")
    else:
        print("Tous les serveurs du catalogue sont déjà là, rien à faire.")


if __name__ == "__main__":
    main()
