# Contrat d'API

Ce que le frontend et le backend se promettent. On l'écrit avant de coder une route, et on le met à jour dans la même PR quand elle change.

Ce document couvre les personnages. Les comptes, les histoires, « Qui traîne ici ? » et la modération viendront ensuite.

## Conventions

- Les chemins sont ceux qu'appelle le frontend. Le préfixe `/api` est retiré avant d'arriver au backend : `/api/characters` y devient `/characters`.
- Tout est en JSON, avec des noms en `snake_case`. Les dates sont en ISO 8601, en UTC.
- Être connecté, c'est avoir un cookie de session valide (décision 8).
- Une erreur renvoie `{"detail": "message lisible"}`. Une erreur de validation renvoie le format de FastAPI, avec la liste des champs fautifs.

| Code | Quand |
|---|---|
| 401 | il faut être connecté |
| 403 | connecté, mais pas le droit |
| 404 | n'existe pas, ou existe mais ne doit pas être visible |
| 409 | conflit avec l'état actuel, par exemple un quatrième lieu |
| 422 | données invalides |

Un contenu masqué par la modération répond 404 à ceux qui n'ont pas le droit de le voir, pas 403. Ça évite de confirmer qu'il existe.

## Ce qu'on ne renvoie jamais

Aucune réponse ne contient de `user_id`, ni rien qui permette de relier deux personnages au même compte, sauf pour leur propriétaire (décision 6 et invariants de `permissions.md`).

## Le personnage

### Fiche complète

```json
{
  "id": 42,
  "server": {"id": 3, "game": "dofus", "name": "Ombrelune"},
  "is_npc": false,
  "name": "Maëlis Sombrefeu",
  "pronoun": "elle",
  "ingame_name": "Maelis-Sombrefeu",
  "class": "Crâ",
  "level": 142,
  "avatar": "archere-3",
  "seal": "fleche-brisee-sang",
  "hook": "Si c'est pour l'arc, il n'est pas à vendre.",
  "appearance": "Grande, cape de voyage râpée…",
  "personality": "Polie avec tout le monde, confiante avec personne.",
  "backstory": "Fille d'un archer de la milice d'Astrub…",
  "goals": "Le nom de celui qui a signé l'ordre.",
  "flaws": "La rancune.",
  "rumors": "On dit qu'elle paie sa chambre avec des kamas qui ne sont pas à elle.",
  "ooc_note": "Partante pour de l'enquête.",
  "play_days": [1, 3, 5],
  "play_periods": ["evening"],
  "hangouts": [
    {"id": 7, "area": "Astrub", "x": 5, "y": -18, "label": "Taverne du Bouftou Ivre", "habits": "Accoudée au comptoir."}
  ],
  "inactive": false,
  "inactive_note": null,
  "created_at": "2026-11-23T10:00:00Z",
  "updated_at": "2026-11-23T10:00:00Z"
}
```

Le propriétaire, les modérateurs et les admins reçoivent en plus :

- `hidden` : `true` si la fiche est masquée par la modération ;
- `is_mine` : `true` pour le propriétaire, ce qui permet au frontend d'afficher les boutons de modification.

### Résumé, pour les listes

```json
{
  "id": 42,
  "server": {"id": 3, "game": "dofus", "name": "Ombrelune"},
  "name": "Maëlis Sombrefeu",
  "pronoun": "elle",
  "class": "Crâ",
  "level": 142,
  "avatar": "archere-3",
  "seal": "fleche-brisee-sang",
  "hook": "Si c'est pour l'arc, il n'est pas à vendre.",
  "play_days": [1, 3, 5],
  "play_periods": ["evening"],
  "inactive": false
}
```

### Champs et limites

Seuls `name` et `server_id` sont obligatoires à la création. Tout le reste peut être vide (`null`, ou une liste vide).

| Champ | Règle |
|---|---|
| `name` | 2 à 40 caractères, pas forcément unique |
| `server_id` | un serveur actif |
| `pronoun` | `elle`, `il` ou `null` (tournures neutres) |
| `ingame_name` | 40 caractères au plus |
| `class` | 30 caractères au plus |
| `level` | `null` ou un entier à partir de 1 |
| `avatar`, `seal` | un identifiant de la liste prédéfinie |
| `hook` | 200 caractères au plus |
| `appearance`, `personality`, `goals`, `flaws`, `rumors` | 2 000 caractères au plus chacun |
| `backstory` | 10 000 caractères au plus |
| `ooc_note` | 500 caractères au plus |
| `play_days` | entiers de 1 (lundi) à 7, sans doublon |
| `play_periods` | parmi `morning`, `afternoon`, `evening`, `night`, sans doublon |
| `inactive_note` | 200 caractères au plus |
| `hangouts` | 3 au plus, voir plus bas |

Les longueurs des textes sont un premier jet, à ajuster après l'alpha.

## Routes

### Lister les personnages

`GET /api/characters`

Pour l'annuaire (story 4). Accessible sans compte.

| Paramètre | Rôle |
|---|---|
| `server_id` | obligatoire, le serveur affiché |
| `day` | facultatif, de 1 à 7 : ceux qui jouent ce jour-là |
| `period` | facultatif : ceux qui jouent sur ce créneau |
| `include_inactive` | facultatif, `false` par défaut : inclure ceux en retrait (story 7) |
| `limit`, `offset` | pagination, `limit` vaut 50 par défaut et 100 au plus |

Réponse 200 :

```json
{"items": [{"id": 42, "name": "Maëlis Sombrefeu", "…": "…"}], "total": 14}
```

Les éléments sont des résumés, triés par nom. Les fiches masquées n'y sont jamais.

Erreurs : 404 si le serveur n'existe pas, 422 si un paramètre est invalide.

### Lire une fiche

`GET /api/characters/{id}`

Accessible sans compte (story 3). Une fiche en retrait reste lisible, avec `inactive: true`.

Réponse 200 : la fiche complète.

Erreurs : 404 si elle n'existe pas, ou si elle est masquée et qu'on n'est ni son propriétaire, ni modérateur, ni admin.

### Lister mes personnages

`GET /api/me/characters`

Pour la barre de mes personnages. Il faut être connecté.

Réponse 200 : `{"items": […]}`, les résumés de tous mes personnages, en retrait et masqués compris, avec `hidden` et `is_mine`.

Erreurs : 401.

### Créer un personnage

`POST /api/characters`

Il faut être connecté (story 2).

Corps : `name` et `server_id`, plus n'importe quel champ facultatif. `hangouts` se gère à part, voir plus bas.

Réponse 201 : la fiche complète, avec l'en-tête `Location: /api/characters/{id}`.

Erreurs : 401, 422 (champ invalide ou serveur inexistant ou inactif).

`is_npc` ne peut être mis à `true` que par un admin, un joueur qui l'envoie reçoit un 403. Un PNJ n'a pas de propriétaire (décision 5).

### Modifier un personnage

`PATCH /api/characters/{id}`

Seul le propriétaire peut modifier sa fiche. Pour un PNJ, ce sont les admins.

Corps : uniquement les champs à changer. Envoyer `null` vide un champ facultatif. `name` ne peut pas être vidé.

La mise en retrait passe aussi par ici (story 7) :

```json
{"inactive": true, "inactive_note": "Parti en mer pour quelques semaines."}
```

et le retour :

```json
{"inactive": false}
```

Revenir efface `inactive_note`.

Réponse 200 : la fiche complète à jour.

Erreurs : 401, 403 si ce n'est pas mon personnage, 404, 422.

Changer de serveur n'est pas permis : `server_id` est refusé avec un 422. Un personnage qui change de serveur, c'est une nouvelle fiche.

### Remplacer les lieux

`PUT /api/characters/{id}/hangouts`

On envoie la liste complète, qui remplace l'ancienne. C'est plus simple qu'une route par lieu pour trois éléments au plus.

Corps :

```json
[
  {"area": "Astrub", "x": 5, "y": -18, "label": "Taverne du Bouftou Ivre", "habits": "Accoudée au comptoir."}
]
```

| Champ | Règle |
|---|---|
| `area` | obligatoire, 40 caractères au plus |
| `x`, `y` | obligatoires, entiers |
| `label` | 60 caractères au plus |
| `habits` | 200 caractères au plus |

Deux lieux d'un même personnage ne peuvent pas avoir les mêmes `area`, `x` et `y`. Une liste vide efface tous les lieux.

Réponse 200 : la liste enregistrée, avec les `id`.

Erreurs : 401, 403, 404, 409 au-delà de trois lieux, 422.

### Supprimer un personnage

`DELETE /api/characters/{id}`

Le propriétaire, ou un admin.

Réponse 204, sans corps. Les lieux partent avec la fiche. Les histoires signées par ce personnage restent, sans signature (`character_id` passe à `NULL`).

Erreurs : 401, 403, 404.

## Les serveurs

`GET /api/servers`

Pour les listes déroulantes. Accessible sans compte.

Réponse 200 :

```json
{"items": [{"id": 3, "game": "dofus", "name": "Ombrelune"}]}
```

Seuls les serveurs actifs sont listés, triés par jeu puis par nom.

## Plus tard

Après ce contrat :

- les comptes : inscription, connexion, mot de passe oublié, suppression ;
- « Qui traîne ici ? » : les lieux d'un serveur et leurs habitués ;
- les histoires ;
- la modération : masquer, signaler, voir à qui appartient un personnage.
