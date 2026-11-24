# Permissions

Les capacités de chaque rôle sont écrites une seule fois, dans `backend/src/backend/accounts/roles.py`, et testées dans `tests/test_roles.py`. Ce document doit dire la même chose.

| Action | Visiteur | Joueur | Propriétaire | Modérateur | Admin |
|---|:-:|:-:|:-:|:-:|:-:|
| Lire une fiche publiée | oui | oui | oui | oui | oui |
| Lire une histoire publiée | non | oui | oui | oui | oui |
| Lire un brouillon | non | non | oui | non | non |
| Lire un contenu masqué | non | non | oui | oui | oui |
| Créer personnage ou histoire | non | oui | oui | oui | oui |
| Modifier un contenu, ses lieux, son retrait | non | non | oui | non | non |
| Supprimer un contenu | non | non | oui | non | oui |
| Signaler | non | oui | non | oui | oui |
| Masquer, traiter un signalement | non | non | non | oui | oui |
| Suspendre, bannir | non | non | non | oui | oui |
| Retirer le droit de signaler | non | non | non | oui | oui |
| Lire le journal de modération | non | non | non | oui | oui |
| Savoir quel compte possède un personnage | non | non | oui | oui | oui |
| Gérer les PNJ | non | non | non | non | oui |
| Gérer les serveurs | non | non | non | non | oui |
| Nommer modérateurs et admins | non | non | non | non | oui |

« Propriétaire » n'est pas un rôle : c'est le joueur à qui appartient le contenu. Ce qu'il peut faire tient à la propriété, pas à une capacité.

## Capacités

| Capacité | Ce qu'elle permet | Modérateur | Admin |
|---|---|:-:|:-:|
| `see_hidden` | Lire un contenu masqué | oui | oui |
| `see_owner` | Savoir quel compte possède un personnage | oui | oui |
| `moderate` | Masquer un contenu, traiter un signalement | oui | oui |
| `ban` | Bannir un compte | oui | oui |
| `delete_any` | Supprimer le contenu d'un autre | non | oui |
| `manage_npcs` | Créer, modifier et supprimer les PNJ | non | oui |
| `manage_servers` | Ajouter, fermer ou fusionner des serveurs | non | oui |
| `manage_roles` | Nommer ou retirer modérateurs et admins | non | oui |

`GET /api/me` donne au site la liste de la personne connectée. Le site s'en sert pour montrer les bons boutons, le serveur revérifie à chaque requête.

Les modérateurs valent pour tout le site. S'ils deviennent propres à un serveur, la portée s'ajoutera dans `roles.py`, sans toucher aux routes.

## Qui agit sur qui
- On ne bannit et on ne masque que quelqu'un de rang inférieur : un modérateur n'agit pas sur un autre modérateur ni sur un admin.
- Le dernier admin non banni ne peut pas être rétrogradé.
- Un compte banni n'a plus aucune capacité, quel que soit son rôle.

## Le premier admin

```
uv run python -m backend.admin promote <adresse> --role admin
uv run python -m backend.admin team
```

`promote` sert aussi à rétrograder (`--role user`). `team` liste les modérateurs et les admins.

## Invariants
- Aucune réponse publique ne contient de user_id.
- Le serveur vérifie qu'un personnage appartient au compte avant d'agir en son nom.
- Le rôle ne peut pas être choisi à l'inscription.
- Une route demande une capacité, jamais un nom de rôle.

## Après la V1
- Les favoris ne sont visibles que de leur propriétaire.
- Une implication est visible une fois acceptée. Elle l'est d'office pour ses propres personnages.
- Un personnage impliqué peut se retirer à tout moment.
