"""Les aperçus de liens (#53) : ce que Discord, Slack ou WhatsApp affichent d'un lien.

Leurs robots lisent la page sans JavaScript : le site, lui, se construit en JavaScript.
Caddy leur envoie donc ces petites pages, faites seulement des balises d'aperçu
(Open Graph). Les humains reçoivent le site, comme d'habitude.

On n'y montre que ce qu'un visiteur voit déjà : une fiche publique, et d'une histoire
seulement qui la signe, ni son titre ni son texte (réservés aux membres). Une fiche ou
une histoire masquée, supprimée ou inconnue donne l'aperçu du site, sans plus.
"""

from html import escape

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from backend.characters.classes import CLASS_LABELS
from backend.characters.models import Character
from backend.characters.routes import load_character
from backend.config import settings
from backend.db import SessionDep
from backend.stories.models import Story
from backend.text import of_name

router = APIRouter(prefix="/preview", tags=["previews"], include_in_schema=False)

SITE = "tRoolPlay"
SITE_LINE = "Le panneau des rôlistes de Dofus : des fiches, des histoires, et qui croiser en jeu."
# La cire du site, pour la barre de couleur de l'aperçu.
COLOR = "#7a2e1c"


def page(
    path: str, title: str, description: str, kind: str = "website"
) -> HTMLResponse:
    """Une page faite pour les robots d'aperçu, tout échappé."""
    url = f"{settings.site_url}{path}"
    tags = {
        "og:site_name": SITE,
        "og:type": kind,
        "og:title": title,
        "og:description": description,
        "og:url": url,
        "og:image": f"{settings.site_url}/apercu.png",
        "og:image:alt": "Le sceau de tRoolPlay sur le bois du panneau",
        "og:locale": "fr_FR",
    }
    meta = "\n".join(
        f'    <meta property="{name}" content="{escape(value)}">'
        for name, value in tags.items()
    )
    return HTMLResponse(
        f"""<!doctype html>
<html lang="fr">
  <head>
    <meta charset="utf-8">
    <title>{escape(title)}</title>
    <meta name="description" content="{escape(description)}">
{meta}
    <meta name="twitter:card" content="summary">
    <meta name="theme-color" content="{COLOR}">
  </head>
  <body><a href="{escape(url)}">{escape(title)}</a></body>
</html>
"""
    )


def site(path: str) -> HTMLResponse:
    return page(path, SITE, SITE_LINE)


def visible_character(session, character_id: int) -> Character | None:
    try:
        return load_character(session, character_id, None)
    except HTTPException:
        return None


@router.get("/personnages/{character_id}", response_class=HTMLResponse)
def character_preview(character_id: int, session: SessionDep) -> HTMLResponse:
    path = f"/personnages/{character_id}"
    character = visible_character(session, character_id)
    if character is None:
        return site(path)
    facts = [
        character.server.name if character.server else None,
        " ".join(
            part
            for part in (
                CLASS_LABELS.get(character.class_) if character.class_ else None,
                f"niv. {character.level}" if character.level else None,
            )
            if part
        )
        or None,
    ]
    line = " · ".join(f for f in facts if f)
    hook = f"« {character.hook} »" if character.hook else None
    description = " — ".join(part for part in (hook, line) if part) or SITE_LINE
    return page(path, character.name, description, kind="profile")


@router.get("/histoires/{story_id}", response_class=HTMLResponse)
def story_preview(story_id: int, session: SessionDep) -> HTMLResponse:
    path = f"/histoires/{story_id}"
    story = session.scalars(
        select(Story)
        .where(
            Story.id == story_id,
            Story.published_at.is_not(None),
            Story.hidden_at.is_(None),
        )
        .options(selectinload(Story.character))
    ).one_or_none()
    character = (
        visible_character(session, story.character_id)
        if story is not None and story.character_id is not None
        else None
    )
    if character is None:
        return site(path)
    return page(
        path,
        f"Une histoire {of_name(character.name)}",
        f"Réservée aux membres de {SITE}.",
        kind="article",
    )
