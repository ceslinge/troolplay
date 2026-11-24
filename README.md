# TroolPlay (nom de code)

Un lieu où les rôlistes de Dofus présentent leurs personnages, racontent leurs histoires et découvrent où se croiser en jeu.

**Le site dit qui, où et plutôt quand. La rencontre se fait en jeu.**

> Projet de fan non officiel et non commercial, sans affiliation avec Ankama.

**État : alpha en cours.** Comptes, fiches, annuaire, « Qui traîne ici ? » et accueil fonctionnent en local. Pas encore en ligne.

## Stack envisagée
- Front : React, TypeScript, Vite
- Back : FastAPI, SQLAlchemy, Alembic
- Base : PostgreSQL
- Production : VPS, Docker Compose, Caddy

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
- Pages légales, brouillons : [mentions](docs/legal/mentions-legales.md), [confidentialité](docs/legal/confidentialite.md), [règles d'usage](docs/legal/regles.md), [charte de modération](docs/legal/moderation.md)
- [Décisions](docs/decisions/README.md)
