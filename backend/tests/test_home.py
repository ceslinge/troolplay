from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.accounts.models import User
from backend.characters.models import Character, CharacterHangout
from backend.home import clock
from backend.servers.models import GameServer

THURSDAY_EVENING = datetime(2026, 11, 26, 21, 30, tzinfo=clock.PARIS)


@pytest.fixture
def thursday_evening(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(clock, "now_in_paris", lambda: THURSDAY_EVENING)


def add(
    session: Session, user: User, server: GameServer, name: str, **fields
) -> Character:
    character = Character(user_id=user.id, server_id=server.id, name=name, **fields)
    session.add(character)
    session.flush()
    return character


def place(session: Session, character: Character, label: str) -> None:
    session.add(
        CharacterHangout(
            character_id=character.id, area="Astrub", x=len(label), y=0, label=label
        )
    )
    session.flush()


@pytest.mark.parametrize(
    ("hour", "period"),
    [
        (6, "morning"),
        (11, "morning"),
        (12, "afternoon"),
        (18, "evening"),
        (23, "evening"),
        (0, "night"),
        (5, "night"),
    ],
)
def test_the_period_follows_the_hour(hour: int, period: str) -> None:
    assert clock.period_of(datetime(2026, 11, 26, hour, tzinfo=clock.PARIS)) == period


@pytest.mark.usefixtures("thursday_evening")
def test_right_now_counts_who_usually_plays_at_this_hour(
    session: Session,
    client: TestClient,
    user: User,
    server: GameServer,
) -> None:
    taverne = add(session, user, server, "Ici", play_days=[4], play_periods=["evening"])
    quais = add(
        session,
        user,
        server,
        "Aussi",
        play_days=[4, 5],
        play_periods=["evening", "night"],
    )
    other = add(
        session, user, server, "Encore", play_days=[4], play_periods=["evening"]
    )
    add(session, user, server, "Pas ce jour", play_days=[5], play_periods=["evening"])
    add(
        session, user, server, "Pas ce créneau", play_days=[4], play_periods=["morning"]
    )
    add(
        session,
        user,
        server,
        "En retrait",
        play_days=[4],
        play_periods=["evening"],
        inactive_at=datetime.now(UTC),
    )
    add(
        session,
        user,
        server,
        "Masqué",
        play_days=[4],
        play_periods=["evening"],
        hidden_at=datetime.now(UTC),
    )
    place(session, taverne, "Taverne de test")
    place(session, other, "Taverne de test")
    place(session, quais, "Quais de test")

    right_now = client.get("/home", params={"server_id": server.id}).json()["right_now"]

    assert right_now["day"] == 4
    assert right_now["period"] == "evening"
    assert right_now["count"] == 3
    assert right_now["places"] == ["Taverne de test", "Quais de test"]


def test_a_closed_or_unknown_server_falls_back_to_an_open_one(
    session: Session, client: TestClient, server: GameServer
) -> None:
    server.is_active = False
    session.flush()

    for server_id in (server.id, 999999999):
        response = client.get("/home", params={"server_id": server_id})
        assert response.status_code == 200
        right_now = response.json()["right_now"]
        assert right_now is None or right_now["server"]["id"] != server.id


def test_a_blank_hook_is_never_overheard(
    session: Session, client: TestClient, user: User, server: GameServer
) -> None:
    add(session, user, server, "Muet", hook="   ")

    # Sur une base vide, la seule réplique est vide : l'API ne doit alors rien citer du tout.
    answers = [client.get("/home/overheard").json() for _ in range(30)]

    assert all(answer is None or answer["hook"].strip() for answer in answers)


def test_overheard_never_quotes_a_hidden_or_inactive_character(
    session: Session, client: TestClient, user: User, server: GameServer
) -> None:
    add(
        session,
        user,
        server,
        "Masqué",
        hook="Réplique masquée de test",
        hidden_at=datetime.now(UTC),
    )
    add(
        session,
        user,
        server,
        "Absent",
        hook="Réplique en retrait de test",
        inactive_at=datetime.now(UTC),
    )
    add(session, user, server, "Bavard", hook="Réplique visible de test")

    quotes = {client.get("/home/overheard").json()["hook"] for _ in range(30)}

    assert "Réplique masquée de test" not in quotes
    assert "Réplique en retrait de test" not in quotes


def test_the_newest_sheets_come_first_without_hidden_ones_or_npcs(
    session: Session, client: TestClient, user: User, server: GameServer
) -> None:
    add(session, user, server, "Discret", hidden_at=datetime.now(UTC))
    session.add(Character(is_npc=True, name="Gardien de test"))
    newest = add(session, user, server, "Tout neuf")

    recent = [c["name"] for c in client.get("/home").json()["recent"]]

    assert recent[0] == newest.name
    assert "Discret" not in recent
    assert "Gardien de test" not in recent


def test_the_home_never_reveals_owners(
    client: TestClient, user: User, server: GameServer, session: Session
) -> None:
    add(session, user, server, "Bavard", hook="Une réplique de test")

    response = client.get("/home")

    assert "user_id" not in response.text
    assert user.email not in response.text


def test_freshly_pinned_shows_one_character_per_player(
    session: Session, client: TestClient, user: User, server: GameServer, make_member
) -> None:
    for number in range(4):
        add(session, user, server, f"Rafale {number}")
    other = make_member("autre.joueur.test@example.com")
    add(session, other, server, "Solitaire")

    recent = [c["name"] for c in client.get("/home").json()["recent"]]

    assert recent[:2] == ["Solitaire", "Rafale 3"]
    assert not {"Rafale 0", "Rafale 1", "Rafale 2"} & set(recent)


def test_the_counter_draws_a_player_before_a_character(
    session: Session, client: TestClient, user: User, server: GameServer, make_member
) -> None:
    # Sur une base vide : un joueur bavard avec 30 répliques, un autre avec une seule.
    for number in range(30):
        add(
            session, user, server, f"Bavard {number}", hook=f"Réplique bavarde {number}"
        )
    other = make_member("discret.test@example.com")
    add(session, other, server, "Discret", hook="Réplique discrète de test")

    names = [client.get("/home/overheard").json()["name"] for _ in range(80)]

    # Par personnage, Discret sortirait une fois sur 31. Par joueur, une fois sur deux
    # (ou moins s'il y a d'autres joueurs en base) : il doit sortir.
    assert "Discret" in names
