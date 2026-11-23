# TroolPlay (nom de code)

Un lieu où les rôlistes de Dofus présentent leurs personnages, racontent leurs histoires et découvrent où se croiser en jeu.

**Le site dit qui, où et plutôt quand. La rencontre se fait en jeu.**

> Projet de fan non officiel et non commercial, sans affiliation avec Ankama.

**État : fondations.** Le backend parle à Postgres, le frontend au backend, la CI vérifie les deux. Pas encore de fonctionnalité.

## Stack envisagée
- Front : React, TypeScript, Vite
- Back : FastAPI, SQLAlchemy, Alembic
- Base : PostgreSQL
- Production : VPS, Docker Compose, Caddy

## Documentation
- [Cadrage](docs/CADRAGE.md)
- [Feuille de route](docs/ROADMAP.md)
- [Base de données](docs/database.md)
- [Permissions](docs/permissions.md)
- [Contrat d'API](docs/api.md)
- [Décisions](docs/decisions/README.md)
