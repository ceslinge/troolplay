"""Le masquage automatique : quand assez de membres fiables signalent un même contenu,
il est caché en attendant qu'un modérateur regarde (décidé le 2026-11-24, #51).

Ce n'est pas une sanction : le contenu reste lisible par son auteur, rien n'est effacé,
rien ne touche le compte. L'auteur est prévenu, l'équipe alertée. Un modérateur confirme,
ou rétablit ; un signalement jugé abusif fait perdre leur poids à ses signaleurs pour la suite.
"""

from datetime import UTC, datetime, timedelta

from fastapi import BackgroundTasks
from sqlalchemy import exists, func, select
from sqlalchemy.orm import Session, aliased

from backend.accounts import emails
from backend.accounts.models import User
from backend.accounts.roles import Role
from backend.characters.models import Character
from backend.config import settings
from backend.moderation.models import ModerationAction, Report
from backend.stories.models import Story

AUTO_REASON = "Masqué automatiquement : plusieurs membres l'ont signalé. En attente d'un modérateur."


def trusted_reporters(session: Session, column, target_id: int) -> int:
    """Les signaleurs distincts, et fiables, des signalements en attente sur ce contenu."""
    now = datetime.now(UTC)
    old_enough = now - timedelta(days=settings.auto_hide_min_account_days)
    past = aliased(Report)
    return (
        session.scalar(
            select(func.count(func.distinct(Report.reporter_id)))
            .join(User, User.id == Report.reporter_id)
            .where(
                column == target_id,
                Report.handled_at.is_(None),
                User.email_verified_at.is_not(None),
                User.created_at <= old_enough,
                User.report_banned_at.is_(None),
                User.active(now),
                # Un seul signalement jugé abusif, et ses signalements ne comptent plus ici.
                ~exists().where(
                    past.reporter_id == User.id, past.decision == "abusive"
                ),
            )
        )
        or 0
    )


def was_auto_hidden(
    session: Session, character_id: int | None, story_id: int | None
) -> bool:
    """Le dernier masquage ou rétablissement de ce contenu est-il un masquage automatique ?"""
    column = (
        ModerationAction.target_character_id
        if character_id is not None
        else ModerationAction.target_story_id
    )
    last = session.scalar(
        select(ModerationAction.action)
        .where(
            column == (character_id if character_id is not None else story_id),
            ModerationAction.action.in_(("hide", "unhide", "auto_hide")),
        )
        .order_by(ModerationAction.created_at.desc(), ModerationAction.id.desc())
        .limit(1)
    )
    return last == "auto_hide"


def maybe_hide(
    session: Session,
    content: Character | Story,
    background: BackgroundTasks,
) -> bool:
    """Après un signalement : masquer si le seuil est atteint. Renvoie vrai si masqué."""
    if content.hidden_at is not None:
        return False
    is_character = isinstance(content, Character)
    column = Report.target_character_id if is_character else Report.target_story_id
    if trusted_reporters(session, column, content.id) < settings.auto_hide_reporters:
        return False

    content.hidden_at = datetime.now(UTC)
    session.add(
        ModerationAction(
            actor_id=None,
            action="auto_hide",
            reason=AUTO_REASON,
            target_user_id=content.user_id,
            target_character_id=content.id if is_character else None,
            target_story_id=None if is_character else content.id,
        )
    )

    name = content.name if is_character else content.title
    what = "Ta fiche" if is_character else "Ton histoire"
    owner = session.get(User, content.user_id) if content.user_id else None
    if owner is not None:
        background.add_task(
            emails.send_email,
            owner.email,
            f"{what} « {name} » est en attente de vérification",
            f"Plusieurs membres ont signalé {what.lower()} « {name} ». Elle est cachée aux "
            "autres le temps qu'un modérateur la regarde. Ce n'est pas une sanction : tu la "
            "vois toujours, tu peux la modifier, et ton compte ne change pas.\n\n"
            "Si le signalement n'est pas fondé, elle sera rétablie et tu seras prévenu·e.\n\n"
            f"La charte de modération : {settings.site_url}/moderation",
        )

    kind = "personnage" if is_character else "histoire"
    link = f"{settings.site_url}/equipe/signalements/{kind}/{content.id}"
    team = session.scalars(
        select(User).where(
            User.role.in_((Role.MODERATOR, Role.ADMIN)), User.active(datetime.now(UTC))
        )
    )
    for member in team:
        background.add_task(
            emails.send_email,
            member.email,
            f"Masquage automatique : « {name} »",
            f"{'Une fiche' if is_character else 'Une histoire'} vient d'être masquée "
            f"automatiquement après plusieurs signalements. À regarder dès que possible :\n\n{link}",
        )
    return True
