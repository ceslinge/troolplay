from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend import demo
from backend.characters.models import Character


def count_characters(session: Session) -> int:
    return session.scalar(select(func.count()).select_from(Character)) or 0


def test_demo_data_is_loaded_only_once(session: Session) -> None:
    before = count_characters(session)

    loaded = demo.load(session)
    assert demo.load(session) is False

    added = len(demo.CHARACTERS) if loaded else 0
    assert count_characters(session) == before + added
