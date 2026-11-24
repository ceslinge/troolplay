FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.12 /uv /bin/uv
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy PATH="/app/.venv/bin:$PATH"

WORKDIR /app
# Les dépendances d'abord : elles changent rarement, l'image se reconstruit vite.
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --locked --no-dev --no-install-project
COPY alembic.ini ./
COPY migrations ./migrations
COPY src ./src
RUN uv sync --locked --no-dev

RUN useradd --system --no-create-home app
USER app

# Au démarrage : la base à jour, les serveurs officiels, puis l'API.
# --proxy-headers : derrière Caddy, l'adresse du joueur (et non celle de Caddy) sert aux limites de tentatives.
# Pas de journal d'accès ici : Caddy le tient déjà, et l'efface au bout de 30 jours.
CMD ["sh", "-c", "alembic upgrade head && python -m backend.servers.sync && exec uvicorn backend.main:app --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips '*' --no-access-log"]
