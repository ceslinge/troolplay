from collections.abc import Callable
from datetime import UTC, datetime

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend import admin as admin_cli
from backend.accounts.models import User
from backend.accounts.roles import (
    CAPABILITIES,
    Capability,
    LastAdminError,
    Role,
    can,
    capabilities,
    outranks,
    require,
    set_role,
)
from backend.accounts.sessions import current_user
from backend.characters.models import Character
from backend.db import get_session

C = Capability


# Le tableau de docs/permissions.md, ligne par ligne.


def test_a_player_has_no_team_capability() -> None:
    assert CAPABILITIES[Role.USER] == set()


def test_moderators_watch_over_the_community_without_managing_it() -> None:
    assert CAPABILITIES[Role.MODERATOR] == {
        C.SEE_HIDDEN,
        C.SEE_OWNER,
        C.MODERATE,
        C.BAN,
    }


def test_admins_can_do_everything() -> None:
    assert CAPABILITIES[Role.ADMIN] == set(Capability)


def test_every_role_has_its_capabilities_written_down() -> None:
    assert set(CAPABILITIES) == set(Role)


def test_visitors_and_banned_accounts_can_do_nothing() -> None:
    banned = User(role="admin", banned_at=datetime.now(UTC))

    assert capabilities(None) == set()
    assert capabilities(banned) == set()
    assert not can(banned, C.MANAGE_ROLES)


# Qui agit sur qui.


@pytest.mark.parametrize(
    ("actor", "target", "expected"),
    [
        ("moderator", "user", True),
        ("admin", "moderator", True),
        ("moderator", "moderator", False),
        ("moderator", "admin", False),
        ("admin", "admin", False),
        ("user", "user", False),
    ],
)
def test_one_acts_only_on_a_lower_rank(actor: str, target: str, expected: bool) -> None:
    assert outranks(User(role=actor), User(role=target)) is expected


# La dépendance des routes.


@pytest.fixture
def probe(session: Session) -> Callable[[User | None], TestClient]:
    """Une petite application avec une route qui exige de pouvoir bannir."""
    probe_app = FastAPI()
    probe_app.dependency_overrides[get_session] = lambda: session

    @probe_app.get("/probe", dependencies=[require(C.BAN)])
    def guarded() -> dict[str, bool]:
        return {"ok": True}

    def as_user(user: User | None) -> TestClient:
        if user is not None:
            probe_app.dependency_overrides[current_user] = lambda: user
        return TestClient(probe_app)

    return as_user


@pytest.mark.parametrize(
    ("role", "status"), [("user", 403), ("moderator", 200), ("admin", 200)]
)
def test_a_route_refuses_who_lacks_the_capability(
    probe: Callable[[User | None], TestClient], role: str, status: int
) -> None:
    assert probe(User(role=role)).get("/probe").status_code == status


def test_a_route_asks_visitors_to_log_in(
    probe: Callable[[User | None], TestClient],
) -> None:
    assert probe(None).get("/probe").status_code == 401


# /me dit au site ce que la personne peut faire.


@pytest.mark.parametrize(
    ("role", "expected"),
    [
        ("user", []),
        ("moderator", ["ban", "moderate", "see_hidden", "see_owner"]),
        ("admin", sorted(Capability)),
    ],
)
def test_me_lists_my_capabilities(
    client: TestClient, make_member, log_in_as, role: str, expected: list[str]
) -> None:
    log_in_as(client, make_member("equipe.test@example.com", role=role))

    assert client.get("/me").json()["capabilities"] == expected


# Ce que les capacités changent sur les fiches.


def test_moderators_read_hidden_sheets_and_their_owner_details(
    session: Session, moderator: TestClient, mine: int
) -> None:
    session.get(Character, mine).hidden_at = datetime.now(UTC)
    session.flush()

    body = moderator.get(f"/characters/{mine}").json()

    assert body["hidden"] is True
    assert body["is_mine"] is False


def test_moderators_neither_edit_nor_delete_someone_elses_sheet(
    moderator: TestClient, mine: int
) -> None:
    assert moderator.patch(f"/characters/{mine}", json={"level": 2}).status_code == 403
    assert moderator.delete(f"/characters/{mine}").status_code == 403


def test_admins_delete_someone_elses_sheet_but_do_not_edit_it(
    admin: TestClient, mine: int
) -> None:
    assert admin.patch(f"/characters/{mine}", json={"level": 2}).status_code == 403
    assert admin.delete(f"/characters/{mine}").status_code == 204


def test_npcs_belong_to_those_who_manage_them(
    moderator: TestClient, admin: TestClient
) -> None:
    npc = {"name": "Gardien", "is_npc": True}
    assert moderator.post("/characters", json=npc).status_code == 403

    created = admin.post("/characters", json=npc).json()

    assert (
        moderator.patch(f"/characters/{created['id']}", json={"level": 3}).status_code
        == 403
    )
    assert (
        admin.patch(f"/characters/{created['id']}", json={"level": 3}).status_code
        == 200
    )


# Changer un rôle, et la commande du premier admin.


def test_the_last_admin_cannot_be_demoted(session: Session, make_member) -> None:
    only = make_member("seul.admin@example.com", role="admin")

    with pytest.raises(LastAdminError):
        set_role(session, only, Role.USER)
    assert only.role == "admin"


def test_an_admin_steps_down_once_someone_else_is_admin(
    session: Session, make_member
) -> None:
    first = make_member("premier.admin@example.com", role="admin")
    make_member("second.admin@example.com", role="admin")

    set_role(session, first, Role.MODERATOR)

    assert first.role == "moderator"


def test_a_banned_admin_does_not_count_as_one_in_charge(
    session: Session, make_member
) -> None:
    active = make_member("actif.admin@example.com", role="admin")
    make_member("banni.admin@example.com", role="admin").banned_at = datetime.now(UTC)

    with pytest.raises(LastAdminError):
        set_role(session, active, Role.USER)


def test_promote_finds_the_account_whatever_the_case(
    session: Session, make_member
) -> None:
    make_member("futur.admin@example.com")

    message = admin_cli.promote(session, "  Futur.Admin@Example.com ", Role.ADMIN)

    assert message == "futur.admin@example.com : user → admin."
    assert admin_cli.promote(session, "futur.admin@example.com", Role.ADMIN) == (
        "futur.admin@example.com est déjà admin."
    )


def test_promote_refuses_an_unknown_address(session: Session) -> None:
    with pytest.raises(LookupError):
        admin_cli.promote(session, "personne@example.com", Role.ADMIN)


def test_team_lists_admins_then_moderators(session: Session, make_member) -> None:
    make_member("modo.liste@example.com", role="moderator")
    make_member("admin.liste@example.com", role="admin")
    make_member("joueur.liste@example.com")

    lines = [line for line in admin_cli.team(session) if "liste@" in line]

    assert lines == [
        "admin      admin.liste@example.com",
        "moderator  modo.liste@example.com",
    ]
