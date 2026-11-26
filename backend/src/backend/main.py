from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from backend.accounts.export import router as export_router
from backend.accounts.routes import router as accounts_router
from backend.characters.routes import me_router as my_characters_router
from backend.characters.routes import router as characters_router
from backend.config import settings
from backend.home.routes import router as home_router
from backend.ignores.routes import router as ignores_router
from backend.moderation.contests import me_router as my_decisions_router
from backend.moderation.contests import router as contests_router
from backend.moderation.routes import router as reports_router
from backend.moderation.team import router as moderation_router
from backend.previews.routes import router as previews_router
from backend.servers.places import router as places_router
from backend.servers.routes import router as servers_router
from backend.servers.team import router as server_team_router
from backend.stories.routes import me_router as my_stories_router
from backend.stories.routes import router as stories_router
from backend.support.routes import me_router as my_conversations_router
from backend.support.routes import router as conversations_router

app = FastAPI(
    docs_url="/docs" if settings.api_docs else None,
    redoc_url=None,
    openapi_url="/openapi.json" if settings.api_docs else None,
)

UNSAFE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


@app.middleware("http")
async def check_origin(request: Request, call_next):
    """Contre le CSRF : une requête qui modifie doit venir du site lui-même.

    Un navigateur envoie toujours l'en-tête Origin sur ces requêtes. Sans lui,
    ce n'est pas un navigateur (un test, curl…), et il n'a pas de cookie à voler.
    """
    origin = request.headers.get("origin")
    if (
        request.method in UNSAFE_METHODS
        and origin is not None
        and origin not in settings.allowed_origins
    ):
        return JSONResponse({"detail": "Origine refusée"}, status_code=403)
    return await call_next(request)


app.include_router(accounts_router)
app.include_router(home_router)
app.include_router(characters_router)
app.include_router(my_characters_router)
app.include_router(servers_router)
app.include_router(places_router)
app.include_router(stories_router)
app.include_router(my_stories_router)
app.include_router(reports_router)
app.include_router(moderation_router)
app.include_router(server_team_router)
app.include_router(my_decisions_router)
app.include_router(contests_router)
app.include_router(my_conversations_router)
app.include_router(export_router)
app.include_router(previews_router)
app.include_router(conversations_router)
app.include_router(ignores_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
