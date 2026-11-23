from typing import Any

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.accounts.models import User
from backend.characters.models import Character, CharacterHangout
from backend.servers.models import GameServer


def test_a_player_character_is_saved_with_its_defaults(
    session: Session, user: User, server: GameServer
) -> None:
    character = Character(user_id=user.id, server_id=server.id, name="Maëlis")
    session.add(character)
    session.flush()
    character_id = character.id
    session.expunge_all()

    character = session.get_one(Character, character_id)

    assert character.is_npc is False
    assert character.play_days == []
    assert character.play_periods == []
    assert character.created_at is not None


@pytest.mark.parametrize(
    "fields",
    [
        {"name": "M"},
        {"level": 0},
        {"gender": "iel"},
        {"class_": "Crâ"},
        {"play_days": [8]},
        {"play_periods": ["midi"]},
    ],
)
def test_invalid_values_are_refused(
    session: Session, user: User, server: GameServer, fields: dict[str, Any]
) -> None:
    values = {"user_id": user.id, "server_id": server.id, "name": "Maëlis"} | fields
    session.add(Character(**values))

    with pytest.raises(IntegrityError):
        session.flush()


def test_a_player_character_needs_an_owner_and_a_server(
    session: Session, server: GameServer
) -> None:
    session.add(Character(server_id=server.id, name="Maëlis"))

    with pytest.raises(IntegrityError):
        session.flush()


def test_an_npc_has_no_owner(session: Session, user: User) -> None:
    session.add(Character(user_id=user.id, is_npc=True, name="Gardien"))

    with pytest.raises(IntegrityError):
        session.flush()


def test_the_same_hangout_twice_is_refused(
    session: Session, user: User, server: GameServer
) -> None:
    character = Character(user_id=user.id, server_id=server.id, name="Maëlis")
    session.add(character)
    session.flush()
    for _ in range(2):
        session.add(
            CharacterHangout(character_id=character.id, area="Astrub", x=5, y=-18)
        )

    with pytest.raises(IntegrityError):
        session.flush()


def test_deleting_an_account_deletes_its_characters(
    session: Session, user: User, server: GameServer
) -> None:
    character = Character(user_id=user.id, server_id=server.id, name="Maëlis")
    session.add(character)
    session.flush()
    session.add(CharacterHangout(character_id=character.id, area="Astrub", x=5, y=-18))
    session.flush()

    character_id = character.id
    session.delete(user)
    session.flush()
    session.expunge_all()

    assert session.get(Character, character_id) is None
    hangouts = select(CharacterHangout).where(
        CharacterHangout.character_id == character_id
    )
    assert session.scalars(hangouts).all() == []


def test_two_accounts_cannot_share_an_email_whatever_the_case(
    session: Session, user: User
) -> None:
    session.add(User(email="JOUEUR.TEST@example.com", password_hash="pas-un-vrai-hash"))

    with pytest.raises(IntegrityError):
        session.flush()
