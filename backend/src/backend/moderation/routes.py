from datetime import timedelta

from fastapi import APIRouter, BackgroundTasks, HTTPException
from sqlalchemy import select

from backend.accounts.sessions import CurrentUser
from backend.accounts.throttle import throttle
from backend.characters.models import Character
from backend.characters.routes import field_error, load_character
from backend.characters.schemas import CharacterOut
from backend.db import SessionDep
from backend.moderation.auto import maybe_hide
from backend.moderation.models import Report
from backend.moderation.schemas import ReportIn
from backend.stories.models import Story
from backend.stories.routes import load_story
from backend.stories.schemas import StoryOut

router = APIRouter(prefix="/reports", tags=["moderation"])

REPORT_LIMIT = 10
REPORT_WINDOW = timedelta(hours=1)

THANKS = "Merci : c'est transmis à l'équipe, qui va regarder."


@router.post("", status_code=202)
def report(
    data: ReportIn,
    user: CurrentUser,
    session: SessionDep,
    background: BackgroundTasks,
) -> dict[str, str]:
    """Signaler une fiche ou une histoire. On ne signale que ce qu'on peut lire, et pas le sien."""
    if user.report_banned_at is not None:
        raise HTTPException(
            status_code=403,
            detail="Tu ne peux plus signaler de contenu. Pour prévenir l'équipe, "
            "écris à l'adresse indiquée dans les mentions légales.",
        )
    if data.target == "character":
        character = load_character(session, data.target_id, user)
        content: Character | Story = character
        owner_id = character.user_id
        snapshot = CharacterOut.model_validate(character).model_dump(mode="json")
        target = {"target_character_id": character.id}
        mine_message = "Tu ne peux pas signaler ton propre personnage"
    else:
        story = load_story(session, data.target_id, user)
        content = story
        owner_id = story.user_id
        snapshot = StoryOut.model_validate(story).model_dump(
            mode="json", exclude={"is_mine"}
        )
        target = {"target_story_id": story.id}
        mine_message = "Tu ne peux pas signaler ta propre histoire"

    if owner_id == user.id:
        raise field_error("target_id", mine_message)

    # Le même signalement, encore en attente : on remercie sans le compter deux fois.
    already = session.scalar(
        select(Report.id).where(
            Report.reporter_id == user.id,
            Report.handled_at.is_(None),
            *(getattr(Report, column) == value for column, value in target.items()),
        )
    )
    if already is None:
        throttle(
            session, "report", str(user.id), limit=REPORT_LIMIT, window=REPORT_WINDOW
        )
        session.add(
            Report(
                reporter_id=user.id,
                reported_user_id=owner_id,
                reason=data.reason,
                details=(data.details or "").strip() or None,
                snapshot=snapshot,
                **target,
            )
        )
        session.flush()
        # Assez de membres fiables l'ont signalé : caché en attendant un modérateur.
        maybe_hide(session, content, background)
    session.commit()
    return {"detail": THANKS}
