# Contrat d'API

Ce que le frontend et le backend se promettent. On l'écrit avant de coder une route, et on le met à jour dans la même PR quand elle change.

Ce document couvre les personnages et les comptes. Les histoires, « Qui traîne ici ? » et la modération viendront ensuite.

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
  "gender": "feminine",
  "ingame_name": "Maelis-Sombrefeu",
  "class": "cra",
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
  "gender": "feminine",
  "class": "cra",
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
| `gender` | `feminine`, `masculine` ou `neutral` (par défaut). Sert seulement à accorder les textes du site |
| `ingame_name` | 40 caractères au plus |
| `class` | `null` ou une classe du jeu : `feca`, `osamodas`, `enutrof`, `sram`, `xelor`, `ecaflip`, `eniripsa`, `iop`, `cra`, `sadida`, `sacrieur`, `pandawa`, `roublard`, `zobal`, `steamer`, `eliotrope`, `huppermage`, `ouginak`, `forgelance`, `bellaphone`, si elle existe dans le jeu du serveur. Retro n'a que les douze premières, Touch n'a ni `eliotrope`, ni `huppermage`, ni `ouginak`, ni `forgelance`. Vide, elle reste un mystère |
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
{"items": [{"id": 3, "game": "dofus", "name": "Ombrelune", "classes": ["feca", "osamodas", "…"]}]}
```

Seuls les serveurs actifs sont listés, triés par jeu puis par nom. `classes` donne les classes jouables dans le jeu du serveur, dans l'ordre du jeu.

## Les comptes

Un compte est privé : seul son propriétaire le voit. Il n'est jamais relié publiquement à ses personnages.

### La session

Se connecter, c'est recevoir un cookie `session` :

- `HttpOnly` : JavaScript ne peut pas le lire, un script injecté ne peut donc pas le voler ;
- `Secure` en production : il ne voyage qu'en HTTPS ;
- `SameSite=Lax` : il n'est pas envoyé quand un autre site déclenche une requête vers le nôtre ;
- `Path=/`, valable 30 jours, prolongé à chaque visite.

Il contient un jeton aléatoire de 32 octets. La base n'en garde que l'empreinte (SHA-256), dans la table `sessions` : une fuite de la base ne donne accès à aucune session. Chaque connexion crée un nouveau jeton. La déconnexion supprime la session côté serveur, pas seulement le cookie.

### Ce qui protège les requêtes

- Toute requête qui modifie quelque chose (`POST`, `PATCH`, `PUT`, `DELETE`) doit venir du site lui-même : le serveur vérifie l'en-tête `Origin` et répond 403 sinon. Avec `SameSite=Lax`, c'est la protection contre le CSRF.
- Les droits se vérifient toujours côté serveur, selon `permissions.md`. Le frontend ne fait qu'afficher ce qu'on a le droit de faire.
- Les fiches et les serveurs se lisent sans compte. Les histoires demandent une session : sans elle, leurs routes répondent 401.

### Mots de passe

- De 10 à 128 caractères, sans autre règle imposée : une phrase vaut mieux qu'un mot compliqué.
- Hachés en Argon2id. Jamais stockés, renvoyés ni écrits dans les journaux en clair.

### Liens envoyés par email

Vérification de l'adresse et mot de passe oublié passent par un lien contenant un jeton aléatoire :

- à usage unique ;
- valable 24 heures pour la vérification, 1 heure pour le mot de passe ;
- stocké en empreinte seulement, dans la table `email_tokens`.
- utiliser un lien rend caducs les autres liens du même genre encore en circulation.

En développement, les emails ne partent pas : ils s'affichent dans le terminal du backend.

### Limites contre les abus

| Action | Limite | Au-delà |
|---|---|---|
| Connexion | 5 essais ratés en 15 minutes pour une adresse, 20 pour une IP (une IP peut être partagée) | 429 |
| Inscription | 5 en 1 heure, par IP | 429 |
| Mot de passe oublié, renvoi de vérification | 3 en 1 heure, par adresse | 429, sans le dire à l'écran |

Une réponse 429 porte l'en-tête `Retry-After`, en secondes.

### Ne pas révéler qui est inscrit

L'inscription, le mot de passe oublié et le renvoi de vérification répondent la même chose, que l'adresse existe ou non. Si l'adresse a déjà un compte, c'est son propriétaire qui reçoit un email pour le prévenir. Personne ne peut tester si quelqu'un est inscrit.

## Routes des comptes

### S'inscrire

`POST /api/accounts`

Corps :

```json
{"email": "toi@example.com", "password": "une phrase assez longue", "accept_rules": true, "age_confirmed": true}
```

`accept_rules` (les règles d'usage) et `age_confirmed` (« J'ai au moins 18 ans ») doivent valoir `true`.

Réponse 202 : `{"detail": "Si cette adresse est libre, un lien de vérification vient de partir."}`. Le compte est créé, mais il faut vérifier l'adresse avant de se connecter.

Erreurs : 422 (adresse invalide, mot de passe trop court ou trop long, case non cochée), 429.

### Vérifier son adresse

`POST /api/accounts/verify`

Corps : `{"token": "…"}`, le jeton du lien reçu.

Réponse 204. Erreurs : 400 si le jeton est inconnu, expiré ou déjà utilisé.

`POST /api/accounts/verify/resend` avec `{"email": "…"}` renvoie un lien. Réponse 202, toujours.

### Se connecter

`POST /api/session`

Corps : `{"email": "…", "password": "…"}`

Réponse 204, avec le cookie `session`.

Erreurs :

- 401 « Email ou mot de passe incorrect », sans préciser lequel ;
- 403 si l'adresse n'est pas encore vérifiée, ou si le compte est suspendu. Seulement quand le mot de passe est bon, pour ne rien révéler à un inconnu ;
- 429.

### Se déconnecter

`DELETE /api/session`

Réponse 204, toujours, même sans session : le cookie est effacé et la session supprimée.

### Mon compte

`GET /api/me`

Réponse 200 :

```json
{"email": "toi@example.com", "role": "user", "created_at": "2026-11-23T10:00:00Z"}
```

Erreurs : 401.

### Mot de passe oublié

`POST /api/password/forgot` avec `{"email": "…"}`. Réponse 202, toujours.

`POST /api/password/reset` avec `{"token": "…", "password": "…"}`. Réponse 204. Toutes les sessions du compte sont fermées : si quelqu'un d'autre était connecté, il ne l'est plus. Le lien prouve aussi que l'adresse est la sienne : un compte pas encore vérifié le devient.

Erreurs : 400 (jeton inconnu, expiré ou utilisé), 422.

### Changer de mot de passe

`PATCH /api/me/password` avec `{"current_password": "…", "new_password": "…"}`.

Réponse 204. Les autres sessions sont fermées, celle en cours est gardée.

Erreurs : 401, 403 si le mot de passe actuel est faux, 422.

### Supprimer son compte

`DELETE /api/me` avec `{"password": "…"}`, pour éviter une suppression par erreur ou depuis un ordinateur laissé ouvert.

Réponse 204. Le compte, ses personnages, leurs lieux et ses histoires sont supprimés. Les signalements restent, sans lien vers lui. Le cookie est effacé.

Erreurs : 401, 403 si le mot de passe est faux.

## Plus tard

Après ce contrat :

- l'export de ses données ;
- « Qui traîne ici ? » : les lieux d'un serveur et leurs habitués ;
- les histoires ;
- la modération : masquer, signaler, voir à qui appartient un personnage.
