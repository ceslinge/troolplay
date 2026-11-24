from datetime import UTC, datetime, timedelta
from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from backend.accounts.models import User
from backend.accounts.roles import Capability, can
from backend.accounts.sessions import CurrentUser
from backend.accounts.throttle import throttle
from backend.characters.models import Character
from backend.characters.routes import field_error
from backend.db import SessionDep
from backend.ignores.filters import not_ignored
from backend.stories.models import Story
from backend.stories.schemas import (
    MyStories,
    MyStorySummary,
    StoryCreate,
    StoryList,
    StoryOut,
    StoryOwnedOut,
    StorySummary,
    StoryUpdate,
)

router = APIRouter(prefix="/stories", tags=["stories"])
me_router = APIRouter(prefix="/me", tags=["stories"])

# Écrire beaucoup n'est pas un tort : la limite ne vise que le spam (décision 28).
PUBLISH_LIMIT = 10
PUBLISH_WINDOW = timedelta(days=1)
# Assez pour plusieurs histoires en chantier, pas pour remplir le disque à coups de script.
MAX_DRAFTS = 30
CREATE_LIMIT = 30
CREATE_WINDOW = timedelta(hours=1)

WITH_CHARACTER = selectinload(Story.character).selectinload(Character.server)


def load_story(session: Session, story_id: int, viewer: User) -> Story:
    """Une histoire que cette personne peut lire, ou 404. Un brouillon n'existe que pour son
    auteur, une histoire masquée que pour son auteur et la modération."""
    story = session.scalars(
        select(Story).where(Story.id == story_id).options(WITH_CHARACTER)
    ).one_or_none()
    if story is None:
        raise HTTPException(status_code=404, detail="Histoire introuvable")
    mine = story.user_id == viewer.id
    if story.published_at is None and not mine:
        raise HTTPException(status_code=404, detail="Histoire introuvable")
    if story.hidden_at is not None and not (mine or can(viewer, Capability.SEE_HIDDEN)):
        raise HTTPException(status_code=404, detail="Histoire introuvable")
    return story


def load_mine(session: Session, story_id: int, user: User) -> Story:
    story = load_story(session, story_id, user)
    if story.user_id != user.id:
        raise HTTPException(status_code=403, detail="Ce n'est pas ton histoire")
    return story


def present(story: Story, viewer: User) -> StoryOwnedOut | StoryOut:
    mine = story.user_id == viewer.id
    if mine or can(viewer, Capability.SEE_HIDDEN):
        return StoryOwnedOut.model_validate(story).model_copy(update={"is_mine": mine})
    return StoryOut.model_validate(story)


def check_room_for_a_draft(session: Session, user: User) -> None:
    drafts = session.scalar(
        select(func.count()).where(
            Story.user_id == user.id, Story.published_at.is_(None)
        )
    )
    if drafts is not None and drafts >= MAX_DRAFTS:
        raise HTTPException(
            status_code=409,
            detail=f"Tu as déjà {MAX_DRAFTS} brouillons : publie ou supprime-en un d'abord.",
        )


def check_signature(session: Session, character_id: int, user: User) -> None:
    """On ne signe que de ses propres personnages, en retrait ou non."""
    character = session.get(Character, character_id)
    if character is None or character.user_id != user.id:
        raise field_error("character_id", "Choisis un de tes personnages")


@router.get("")
def list_stories(
    session: SessionDep,
    user: CurrentUser,
    server_id: int | None = None,
    character_id: int | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
    # Les plus anciennes d'abord : lire un personnage depuis le début de son histoire.
    order: Literal["newest", "oldest"] = "newest",
) -> StoryList:
    if (server_id is None) == (character_id is None):
        raise HTTPException(
            status_code=422, detail="Indique un serveur ou un personnage"
        )
    query = (
        select(Story)
        .join(Story.character)
        .where(
            Story.published_at.is_not(None),
            Story.hidden_at.is_(None),
            Character.hidden_at.is_(None),
        )
    )
    if server_id is not None:
        # Les listes du serveur taisent les personnages ignorés ; sur leur fiche, on les a ouverts exprès.
        query = query.where(Character.server_id == server_id, not_ignored(user))
    else:
        query = query.where(Story.character_id == character_id)

    total = session.scalar(select(func.count()).select_from(query.subquery())) or 0
    stories = session.scalars(
        query.options(WITH_CHARACTER)
        .order_by(
            *(
                (Story.published_at.desc(), Story.id.desc())
                if order == "newest"
                else (Story.published_at.asc(), Story.id.asc())
            )
        )
        .limit(limit)
        .offset(offset)
    )
    return StoryList(
        items=[StorySummary.model_validate(s) for s in stories], total=total
    )


@router.get("/{story_id}")
def read_story(
    story_id: int, session: SessionDep, user: CurrentUser
) -> StoryOwnedOut | StoryOut:
    return present(load_story(session, story_id, user), user)


@router.post("", status_code=201)
def create_story(
    data: StoryCreate, user: CurrentUser, session: SessionDep
) -> StoryOwnedOut | StoryOut:
    check_signature(session, data.character_id, user)
    check_room_for_a_draft(session, user)
    throttle(session, "story", str(user.id), limit=CREATE_LIMIT, window=CREATE_WINDOW)
    story = Story(user_id=user.id, **data.model_dump())
    session.add(story)
    session.commit()
    return present(load_story(session, story.id, user), user)


@router.patch("/{story_id}")
def update_story(
    story_id: int, data: StoryUpdate, user: CurrentUser, session: SessionDep
) -> StoryOwnedOut | StoryOut:
    story = load_mine(session, story_id, user)
    changes = data.model_dump(exclude_unset=True)
    # Seule la précision peut s'effacer : le reste se remplace, sans jamais rester vide.
    for field in ("title", "body", "content_warnings", "character_id"):
        if field in changes and changes[field] is None:
            raise field_error(field, "Ce champ ne peut pas être vide")
    if "character_id" in changes:
        check_signature(session, changes["character_id"], user)
    if story.published_at is not None and changes.get("body", story.body).strip() == "":
        raise field_error("body", "Une histoire publiée ne peut pas être vide")
    for field, value in changes.items():
        setattr(story, field, value)
    session.commit()
    return present(load_story(session, story.id, user), user)


@router.post("/{story_id}/publish")
def publish_story(
    story_id: int, user: CurrentUser, session: SessionDep
) -> StoryOwnedOut | StoryOut:
    story = load_mine(session, story_id, user)
    if story.published_at is None:
        if not story.body.strip():
            raise field_error("body", "Écris ton histoire avant de la publier")
        if story.character_id is None:
            raise field_error(
                "character_id", "Choisis un personnage pour signer cette histoire"
            )
        throttle(
            session, "publish", str(user.id), limit=PUBLISH_LIMIT, window=PUBLISH_WINDOW
        )
        story.published_at = datetime.now(UTC)
        session.commit()
    return present(load_story(session, story.id, user), user)


@router.post("/{story_id}/unpublish")
def unpublish_story(
    story_id: int, user: CurrentUser, session: SessionDep
) -> StoryOwnedOut | StoryOut:
    story = load_mine(session, story_id, user)
    if story.published_at is not None:
        check_room_for_a_draft(session, user)
    story.published_at = None
    session.commit()
    return present(load_story(session, story.id, user), user)


@router.delete("/{story_id}", status_code=204)
def delete_story(story_id: int, user: CurrentUser, session: SessionDep) -> None:
    story = load_story(session, story_id, user)
    if story.user_id != user.id and not can(user, Capability.DELETE_ANY):
        raise HTTPException(status_code=403, detail="Ce n'est pas ton histoire")
    session.delete(story)
    session.commit()


@me_router.get("/stories")
def list_my_stories(user: CurrentUser, session: SessionDep) -> MyStories:
    stories = session.scalars(
        select(Story)
        .where(Story.user_id == user.id)
        .options(WITH_CHARACTER)
        .order_by(Story.updated_at.desc(), Story.id.desc())
    )
    return MyStories(items=[MyStorySummary.model_validate(s) for s in stories])
