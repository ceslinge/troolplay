"""Ajoute en base les serveurs du catalogue qui n'y sont pas encore. On peut le relancer sans risque."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.db import SessionLocal
from backend.servers.catalog import SERVERS
from backend.servers.models import GameServer


def sync(session: Session) -> list[tuple[str, str]]:
    """Les serveurs ajoutés. Ceux qui existent déjà, même fermés, ne sont pas touchés :
    un serveur fermé par l'équipe ne doit pas rouvrir tout seul. Un serveur renommé sur le
    site se reconnaît à son nom de catalogue, et un serveur ajouté sur le site à son nom."""
    catalog = {(game, name) for game, names in SERVERS.items() for name in names}
    known: set[tuple[str, str]] = set()
    for server in session.scalars(select(GameServer)):
        # Ajouté sur le site avant d'arriver au catalogue : on le relie à son nom de catalogue,
        # pour qu'un renommage plus tard ne le fasse pas revenir en double.
        if server.catalog_name is None and (server.game, server.name) in catalog:
            server.catalog_name = server.name
        known.add((server.game, server.name))
        if server.catalog_name:
            known.add((server.game, server.catalog_name))
    added = [
        (game, name)
        for game, names in SERVERS.items()
        for name in names
        if (game, name) not in known
    ]
    session.add_all(
        GameServer(game=game, name=name, catalog_name=name) for game, name in added
    )
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
