from fastapi import FastAPI

from backend.characters.routes import router as characters_router
from backend.servers.routes import router as servers_router

app = FastAPI()
app.include_router(characters_router)
app.include_router(servers_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
