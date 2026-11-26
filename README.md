# tRoolPlay

Un lieu où les rôlistes de Dofus présentent leurs personnages, racontent leurs histoires et découvrent où se croiser en jeu.

**Le site dit qui, où et plutôt quand. La rencontre se fait en jeu.**

> Projet de fan non officiel et non commercial, sans affiliation avec Ankama.

**État : alpha en cours.** Comptes, fiches, annuaire, « Qui traîne ici ? », histoires, signalements et modération fonctionnent en local. Pas encore en ligne.

## Stack
- Front : React, TypeScript, Vite
- Back : FastAPI, SQLAlchemy, Alembic
- Base : PostgreSQL
- Production : VPS, Docker Compose, Caddy

## Lancer le projet en local

Il faut [Docker](https://docs.docker.com/get-docker/), [uv](https://docs.astral.sh/uv/) et [Node.js](https://nodejs.org/) 26.

Une seule fois, depuis la racine du dépôt :

```bash
cp .env.example .env              # puis choisir un mot de passe pour la base
docker compose up -d              # la base Postgres, qui repart ensuite seule
cd backend
uv sync
uv run alembic upgrade head
uv run python -m backend.servers.sync
uv run python -m backend.demo     # facultatif : des personnages pour ne pas partir de rien
cd ../frontend
npm install
```

Ensuite, à chaque fois, dans deux terminaux :

```bash
cd backend && uv run fastapi dev src/backend/main.py
cd frontend && npm run dev
```

Le site est sur http://localhost:5173. En local, aucun email ne part : ils s'affichent dans le terminal du backend, liens de vérification compris.

Pour devenir admin, une fois inscrit et l'adresse vérifiée : `cd backend && uv run python -m backend.admin promote <ton-adresse> --role admin`.

Après un `git pull`, relancer `uv run alembic upgrade head` (et `uv sync`, `npm install` si les dépendances ont changé).

### Ouvrir son site local à quelqu'un sur le même réseau

`npm run dev -- --host` rend le site joignable sur `http://<ton-ip>:5173`. Ajouter alors cette adresse dans `.env`, sinon l'API refuse ce qui vient d'elle (protection contre le CSRF), puis relancer le backend :

```
ALLOWED_ORIGINS=["http://localhost:5173","http://<ton-ip>:5173"]
```

## Données

Depuis `backend/` :

- `uv run alembic upgrade head` : met la base à jour.
- `uv run python -m backend.servers.sync` : ajoute les serveurs officiels qui manquent (liste dans `src/backend/servers/catalog.py`). On peut le relancer sans risque ; à lancer après chaque mise à jour de la liste, et à chaque déploiement.
- `uv run python -m backend.demo` : ajoute des personnages de démo, pour le développement seulement.
- `uv run python -m backend.admin promote <adresse> --role admin` : nomme un admin (ou `moderator`, ou `user` pour retirer un rôle). Le dernier admin ne peut pas être rétrogradé. `uv run python -m backend.admin team` liste l'équipe.

## Documentation
- [Cadrage](docs/CADRAGE.md)
- [Feuille de route](docs/ROADMAP.md)
- [Base de données](docs/database.md)
- [Permissions](docs/permissions.md)
- [Contrat d'API](docs/api.md)
- [Déployer](docs/deploy.md)
- Pages légales, brouillons : [mentions](docs/legal/mentions-legales.md), [confidentialité](docs/legal/confidentialite.md), [règles d'usage](docs/legal/regles.md), [charte de modération](docs/legal/moderation.md)
- [Décisions](docs/decisions/README.md)
