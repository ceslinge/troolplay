from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.servers import sync as sync_module
from backend.servers.catalog import SERVERS
from backend.servers.models import GameServer
from backend.servers.sync import sync

CATALOG = {"dofus": ("Serveur A", "Serveur B"), "retro": ("Serveur C",)}


def test_the_catalog_is_well_formed() -> None:
    for game, names in SERVERS.items():
        assert game in ("dofus", "retro", "touch")
        assert len(set(names)) == len(names), game
        assert all(0 < len(name) <= 40 for name in names), game


def test_sync_adds_the_missing_servers(session: Session, monkeypatch) -> None:
    monkeypatch.setattr(sync_module, "SERVERS", CATALOG)
    session.add(GameServer(game="dofus", name="Serveur A"))
    session.flush()

    added = sync(session)

    assert added == [("dofus", "Serveur B"), ("retro", "Serveur C")]
    names = session.scalars(
        select(GameServer.name).where(GameServer.name.like("Serveur _"))
    ).all()
    assert sorted(names) == ["Serveur A", "Serveur B", "Serveur C"]


def test_sync_can_run_twice(session: Session, monkeypatch) -> None:
    monkeypatch.setattr(sync_module, "SERVERS", CATALOG)
    sync(session)

    assert sync(session) == []


def test_sync_does_not_reopen_a_closed_server(session: Session, monkeypatch) -> None:
    monkeypatch.setattr(sync_module, "SERVERS", CATALOG)
    closed = GameServer(game="dofus", name="Serveur A", is_active=False)
    session.add(closed)
    session.flush()

    sync(session)

    session.refresh(closed)
    assert closed.is_active is False


def test_the_same_name_in_another_game_is_another_server(
    session: Session, monkeypatch
) -> None:
    monkeypatch.setattr(sync_module, "SERVERS", {"touch": ("Serveur A",)})
    session.add(GameServer(game="dofus", name="Serveur A"))
    session.flush()

    assert sync(session) == [("touch", "Serveur A")]


def test_a_server_renamed_on_the_site_does_not_come_back(
    session: Session, monkeypatch
) -> None:
    monkeypatch.setattr(sync_module, "SERVERS", CATALOG)
    sync(session)
    renamed = session.scalars(
        select(GameServer).where(GameServer.name == "Serveur A")
    ).one()
    renamed.name = "Serveur A'"
    session.flush()

    assert sync(session) == []
