# Contrat d'API

Ce que le frontend et le backend se promettent. On l'écrit avant de coder une route, et on le met à jour dans la même PR quand elle change.

Ce document couvre les personnages, les histoires et les comptes. La modération viendra ensuite.

## Conventions

- Les chemins sont ceux qu'appelle le frontend. Le préfixe `/api` est retiré avant d'arriver au backend : `/api/characters` y devient `/characters`.
- Tout est en JSON, avec des noms en `snake_case`. Les dates sont en ISO 8601, en UTC.
- Être connecté, c'est avoir un cookie de session valide (décision 8).
- Un champ texte qui exige un contenu (nom, titre, zone, raison) perd ses espaces autour avant d'être vérifié : des espaces seuls sont refusés (422). Les mots de passe sont pris tels quels.
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
| `q` | facultatif, 60 caractères au plus : ceux dont le nom ou le nom en jeu contient ce texte, sans tenir compte des accents ni des majuscules. Vide, il est ignoré |
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

Réponse 200 : `{"items": […]}`, les résumés de tous mes personnages, en retrait et masqués compris, avec `hidden` et `is_mine`. Ils sont dans l'ordre que j'ai choisi ; un nouveau personnage se range au bout. Ceux en retrait ou masqués passent après les autres, dans mon ordre eux aussi.

Erreurs : 401.

### Ranger mes personnages

`PUT /api/me/characters/order`

Corps : `{"ids": [12, 7, 31]}`, tous mes personnages, chacun une fois, dans l'ordre voulu.

Réponse 200 : la liste rangée, comme `GET /api/me/characters`.

Erreurs : 401, 422 si la liste en oublie un, en répète un ou contient celui d'un autre.

### Créer un personnage

`POST /api/characters`

Il faut être connecté (story 2).

Corps : `name` et `server_id`, plus n'importe quel champ facultatif. `hangouts` se gère à part, voir plus bas.

Réponse 201 : la fiche complète, avec l'en-tête `Location: /api/characters/{id}`.

Erreurs : 401, 409 au-delà de 10 personnages par compte (décision 31), 422 (champ invalide, serveur inexistant ou inactif, classe absente du jeu de ce serveur). Les erreurs portent sur le champ concerné, dans le format de FastAPI.

`is_npc` ne peut être mis à `true` que par un admin, un joueur qui l'envoie reçoit un 403. Un PNJ n'a ni propriétaire ni serveur (décision 5) : `server_id` est alors refusé.

Un champ inconnu, comme `user_id`, est refusé avec un 422 plutôt qu'ignoré.

### Modifier un personnage

`PATCH /api/characters/{id}`

Seul le propriétaire peut modifier sa fiche. Pour un PNJ, ce sont les admins.

Corps : uniquement les champs à changer. Envoyer `null` vide un champ facultatif : `gender` revient alors à `neutral`, `play_days` et `play_periods` à une liste vide. `name` ne peut pas être vidé.

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

Un personnage peut changer de serveur, comme en jeu (transfert, fusion, serveur temporaire qui ferme) : `server_id` accepte un serveur ouvert du même jeu. La fiche garde tout. Un autre jeu, un serveur fermé ou `null` sont refusés avec un 422, comme un serveur pour un PNJ.

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
| `area` | obligatoire, de 1 à 40 caractères |
| `x`, `y` | obligatoires, entiers entre -1000 et 1000 |
| `label` | 60 caractères au plus |
| `habits` | 200 caractères au plus |

Deux lieux d'un même personnage ne peuvent pas avoir les mêmes `area`, `x` et `y` : un doublon est refusé avec un 422, sans tenir compte des majuscules ni des espaces autour de `area`. Une liste vide efface tous les lieux.

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
{"items": [{"id": 3, "game": "dofus", "name": "Ombrelune", "classes": ["feca", "osamodas", "…"], "closed": false}]}
```

Seuls les serveurs ouverts sont listés, triés par jeu puis par nom. `classes` donne les classes jouables dans le jeu du serveur, dans l'ordre du jeu. Le serveur d'une fiche porte le même format : `closed` à `true` dit qu'il a été fermé par l'équipe. La fiche reste lisible et modifiable ; on ne crée plus de personnage sur ce serveur, et on n'y déménage plus.

## Qui traîne ici ?

`GET /api/servers/{id}/places`, accessible sans compte. Paramètres facultatifs : `day` et `period`, comme pour l'annuaire.

Réponse 200 : les lieux du serveur où au moins un personnage a ses habitudes, les plus fréquentés d'abord.

```json
{"items": [{"area": "Astrub", "x": 5, "y": -18, "label": "Taverne du Bouftou Ivre", "regulars": [{"character": {"id": 42, "name": "Maëlis", "…": "…"}, "habits": "Accoudée au comptoir."}]}]}
```

Un même lieu est reconnu à sa zone et à ses coordonnées, même écrit différemment d'une fiche à l'autre. Son nom est celui que les fiches lui donnent le plus souvent. Les personnages masqués ou en retrait n'y figurent pas. Erreurs : 404 si le serveur n'existe pas, 422 si un filtre est invalide.

## L'accueil

`GET /api/home`, accessible sans compte. Paramètre facultatif : `server_id`, le serveur de « À cette heure-ci ». Sans lui, le premier serveur actif.

Réponse 200 :

```json
{
  "right_now": {"server": {"id": 3, "name": "Ombrelune", "…": "…"}, "day": 4, "period": "evening", "count": 9, "places": ["Taverne du Bouftou Ivre", "Quais du port"]},
  "overheard": {"character_id": 42, "name": "Maëlis", "server": "Ombrelune", "hook": "Si c'est pour l'arc, il n'est pas à vendre."},
  "recent": [{"id": 42, "name": "Maëlis", "…": "…"}]
}
```

- `right_now` compte les personnages du serveur qui ont l'habitude de jouer ce jour-là et à ce créneau, à l'heure de Paris. C'est déclaratif : ce n'est pas qui est connecté. `places` donne leurs deux lieux les plus fréquentés.
- `overheard` est une réplique d'accroche tirée au hasard : d'abord un joueur, puis une de ses répliques, pour que celui qui a dix personnages ne soit pas dix fois plus entendu. `GET /api/home/overheard` en tire une autre.
- `recent` liste les six dernières fiches, une seule par joueur : la plus récente.

Les fiches masquées, en retrait et les PNJ n'apparaissent dans aucune de ces trois parties, ni les répliques vides. Un `server_id` inconnu ou fermé ne fait pas d'erreur : on retombe sur le premier serveur actif.

## Les histoires

Une histoire appartient à un compte et est signée par un de ses personnages (story 8). Elles se lisent seulement connecté (décision 25) : sans session, toutes ces routes répondent 401.

### L'histoire complète

```json
{
  "id": 12,
  "title": "La nuit où Astrub a brûlé",
  "body": "Le vent tournait. *Encore une nuit sans sommeil*, pensa-t-elle…",
  "character": { "id": 42, "name": "Maëlis", "gender": "feminine", "class": "cra", "avatar": null, "seal": null, "server": { "id": 3, "game": "dofus", "name": "Ombre", "classes": ["…"], "closed": false } },
  "content_warnings": ["death", "violence"],
  "content_note": "Mort d'un personnage aimé",
  "author_note": "Suite de la soirée du 12 à la taverne. Merci à Tobias !",
  "published": true,
  "published_at": "2026-11-24T20:00:00Z",
  "updated_at": "2026-11-24T21:12:00Z",
  "is_mine": false,
  "hidden": false
}
```

- `character` vaut `null` si le personnage qui la signait a été supprimé. Son auteur peut la signer d'un autre de ses personnages.
- `body` est du texte. Le site y met en forme `*italique*` et `**gras**`, rien d'autre : aucun HTML n'est interprété.
- `hidden` n'apparaît que pour l'auteur et la modération.

### Résumé, pour les listes

Le titre, le personnage, les avertissements, `published_at`, `reading_minutes` (le temps de lecture, à 230 mots par minute, une minute au moins), et `excerpt` : les 200 premiers caractères du texte, sans les astérisques de mise en forme. `excerpt` vaut `null` quand l'histoire porte un avertissement : on choisit avant de lire.

### Champs et limites

| Champ | Règle |
|---|---|
| `title` | de 1 à 120 caractères |
| `body` | 50 000 caractères au plus. Peut être vide dans un brouillon, pas à la publication |
| `character_id` | un de mes personnages, en retrait ou non. Obligatoire |
| `content_warnings` | parmi `violence`, `death`, `torture`, `sexual_themes`, `abuse`, `self_harm`, `addiction`, `phobia`, chacun une fois |
| `content_note` | 200 caractères au plus : une précision libre sur ce qui attend le lecteur |
| `author_note` | 1 000 caractères au plus : le mot de l'auteur, hors RP, affiché à part du texte. Absent des résumés |

`sexual_themes` prévient d'un thème, jamais d'une scène explicite : celles-ci restent interdites (règles d'usage).

### Lister les histoires

`GET /api/stories?server_id=3` ou `GET /api/stories?character_id=42`, l'un des deux.

| Paramètre | |
|---|---|
| `server_id` | les histoires des personnages de ce serveur (l'onglet Histoires de la communauté) |
| `character_id` | celles d'un personnage (le bas de sa fiche) |
| `order` | `newest` (par défaut) ou `oldest` : les plus anciennes d'abord, pour lire un personnage depuis le début |
| `limit`, `offset` | 20 par défaut, 100 au plus |

Seulement les histoires publiées, ni masquées ni sans signature, de personnages non masqués. Les plus récentes d'abord. Réponse : `{"items": [...résumés], "total": 37}`.

### Lire une histoire

`GET /api/stories/{id}`. Un brouillon n'est lisible que par son auteur, une histoire masquée par son auteur et la modération : pour les autres, 404.

### Mes histoires

`GET /api/me/stories` : toutes les miennes, brouillons compris, la dernière modifiée d'abord. Chaque résumé y porte aussi `published` et `hidden`.

### Écrire une histoire

`POST /api/stories` avec `character_id`, `title`, et au besoin `body`, `content_warnings`, `content_note`. Elle naît brouillon. Réponse 201 avec l'histoire complète.

Erreurs : 422 si le personnage n'est pas à moi. 409 au-delà de 30 brouillons : il faut en publier ou en supprimer un. 429 au-delà de 30 créations en une heure, contre les scripts.

### Modifier une histoire

`PATCH /api/stories/{id}` avec les champs à changer, son auteur seulement (403 sinon). Une histoire publiée reste publiée : on peut corriger une faute sans la retirer.

### Publier, retirer

- `POST /api/stories/{id}/publish` : la rend lisible par les membres. 422 si son texte est vide ou si elle n'a plus de signature. 10 publications par jour au plus (429 au-delà), contre le spam (décision 28). Republier une histoire déjà publiée ne change rien.
- `POST /api/stories/{id}/unpublish` : elle redevient brouillon. 409 si j'ai déjà 30 brouillons.

Réponse 200 avec l'histoire complète. Son auteur seulement.

### Supprimer une histoire

`DELETE /api/stories/{id}` : son auteur, ou un admin (capacité `delete_any`). Réponse 204.

## Ignorer un personnage

Pour ne plus croiser un personnage, sans que personne soit sanctionné (#112). Connecté.

- `PUT /api/me/ignored/{id}` : l'ignorer. 204, et le refaire ne change rien. 404 si je ne peux pas le lire, 422 si c'est un des miens.
- `DELETE /api/me/ignored/{id}` : ne plus l'ignorer. 204.
- `GET /api/me/ignored` : mes personnages ignorés, résumés, le dernier ignoré d'abord.

Il disparaît alors de mes listes : l'annuaire, « Qui traîne ici ? », les histoires du serveur et l'accueil. Sa fiche et ses histoires restent lisibles par un lien ; sur sa fiche, `ignored: true` me le rappelle, et sa liste d'histoires reste complète. On ignore un personnage, jamais un joueur : tous les personnages d'un compte disparaissant d'un coup diraient qu'ils ont le même joueur (décision 6). Personne d'autre ne sait qui ignore qui.

## Signaler

`POST /api/reports`, connecté, avec :

```json
{"target": "story", "target_id": 12, "reason": "disrespect", "details": "Vise un joueur précis."}
```

| Champ | Règle |
|---|---|
| `target` | `character` ou `story` |
| `target_id` | un contenu que je peux lire : 404 sinon, comme pour le lire |
| `reason` | `off_topic`, `disrespect`, `hate`, `explicit`, `personal_info`, `impersonation`, `spam`, `illegal` ou `other`, d'après la charte de modération |
| `details` | 1 000 caractères au plus. Obligatoire avec `other` |

Réponse 202 : `{"detail": "Merci : c'est transmis à l'équipe, qui va regarder."}`. On ne dit rien de plus : ni à l'auteur du signalement ce qui sera décidé, ni à la personne signalée qui l'a signalée.

- Signaler son propre contenu : 422.
- Signaler encore le même contenu tant que le premier signalement attend : même réponse, rien de plus n'est enregistré.
- 10 signalements par heure au plus (429).
- Le signalement garde une copie du contenu tel qu'on le lit à ce moment-là. Elle sera effacée une fois le signalement traité (#51).
- **Masquage automatique** : quand des signalements en attente sur un même contenu viennent d'au moins 3 membres distincts et fiables (adresse vérifiée, compte de plus de 3 jours, droit de signaler intact, aucun signalement jamais jugé abusif), le contenu est caché en attendant un modérateur. Son auteur le voit toujours et est prévenu par email ; l'équipe est alertée. Les deux seuils se règlent par `AUTO_HIDE_REPORTERS` et `AUTO_HIDE_MIN_ACCOUNT_DAYS`, pour l'essayer en local.

Sans compte, on signale par l'adresse de contact des mentions légales. Un compte à qui la modération a retiré le droit de signaler reçoit 403, avec la même indication.

## La modération

Pour l'équipe seulement : capacité `moderate`, et `ban` pour suspendre (401 sans session, 403 sans la capacité). Un compte s'y désigne par son numéro, jamais par son adresse email. C'est le seul endroit où l'on voit à quel compte appartient un personnage.

Chaque action demande une raison écrite (`reason`, de 3 à 1 000 caractères), s'inscrit au journal, et la personne concernée la reçoit par email avec le lien vers la charte et le moyen de contester. On n'agit que sur un compte de rang inférieur au sien (403 sinon) ; un PNJ, qui n'a pas de joueur, est aux admins.

### Les dossiers

- `GET /api/moderation/cases?status=open` : un dossier par contenu signalé, avec `open_reports`, `total_reports`, les motifs en attente (`reasons`), `last_reported_at` et `auto_hidden`. Les dossiers masqués automatiquement d'abord, puis les plus signalés. `status=closed` : ceux qui n'ont plus rien en attente.
- `GET /api/moderation/cases/{character|story}/{id}` : le dossier, le compte propriétaire, et chaque signalement avec son motif, sa précision, la copie du contenu (tant qu'il n'est pas tranché) et son auteur : numéro de compte, signalements envoyés, jugés fondés, jugés abusifs.
- `POST /api/moderation/cases/{character|story}/{id}/decide` avec `{"decision": "founded" | "no_action" | "abusive", "reason": "…"}` : tranche tout ce qui attend. Les copies sont effacées. Un contenu masqué automatiquement est rétabli par « sans suite » ou « abusif », et son auteur prévenu ; « fondé » le laisse masqué. 409 si rien n'attend.

### Depuis la page d'un contenu

`GET /api/moderation/characters/{id}` et `GET /api/moderation/stories/{id}` : le compte propriétaire, si c'est masqué, et combien de signalements attendent. De quoi agir sans passer par un dossier.

### Masquer, rétablir

`POST /api/moderation/characters/{id}/hide`, `…/unhide`, et de même pour `stories`, avec `{"reason": "…"}`. Masqué, le contenu disparaît pour les autres ; son auteur le voit et le modifie toujours. 409 si c'est déjà le cas.

### Les comptes

- `GET /api/moderation/accounts/{id}` : rôle, création, adresse vérifiée ou non, suspension, droit de signaler, personnages, signalements reçus et envoyés.
- `POST /api/moderation/accounts/{id}/suspend` avec `{"duration": "day" | "week" | "month" | "forever", "reason": "…"}` (capacité `ban`) : les connexions en cours s'arrêtent, la connexion est refusée jusqu'au terme, puis la suspension se lève seule. Les personnages et les histoires restent en ligne.
- `POST /api/moderation/accounts/{id}/reinstate` avec `{"reason": "…"}` : lève la suspension.
- `POST /api/moderation/accounts/{id}/reporting` avec `{"allowed": false, "reason": "…"}` : retire le droit de signaler, ou le rend avec `true`. Le compte ne change pas autrement.

### Les rôles

Capacité `manage_roles`, donc les admins.

- `GET /api/moderation/team` (capacité `moderate`) : les modérateurs et les admins, avec leurs personnages, les admins d'abord.
- `POST /api/moderation/accounts/lookup` avec `{"email": "…"}` : le numéro du compte qui a cette adresse exacte, ou 404. En `POST`, pour qu'une adresse ne passe jamais dans une URL que les journaux du serveur gardent. Aucune route ne liste d'adresses.
- `POST /api/moderation/accounts/{id}/role` avec `{"role": "user" | "moderator" | "admin", "reason": "…"}` : 409 si c'est déjà son rôle, ou si c'est le dernier admin. La personne est prévenue par email. Entre admins, pas de règle de rang : nommer et retirer, c'est le rôle même des admins.

### Les serveurs

Capacité `manage_servers`, donc les admins. Chaque geste demande une raison et va au journal ; personne n'est prévenu par email.

- `GET /api/moderation/servers` : tous les serveurs, fermés compris, avec leur nombre de fiches (`characters`) et d'histoires publiées (`stories`).
- `POST /api/moderation/servers` avec `{"game": "dofus" | "retro" | "touch", "name": "…", "reason": "…"}` : 201, le serveur est ouvert. 422 si un serveur du même jeu porte déjà ce nom (à la casse près).
- `PATCH /api/moderation/servers/{id}` avec `{"name": "…", "reason": "…"}` : renommer. Le journal garde l'ancien nom dans `detail`. Un serveur du catalogue garde son nom d'origine en base (`catalog_name`) : le déploiement suivant ne le recrée pas.
- `POST /api/moderation/servers/{id}/close` et `/reopen` avec `{"reason": "…"}` : 409 s'il l'est déjà.

### Les contestations (#141)

Une personne visée par une décision (`hide`, `auto_hide`, `suspend`, `revoke_reporting`) peut la contester **une fois** : la base le garantit (une ligne de `contests` par décision).

Un compte suspendu se connecte, mais toutes les routes lui restent fermées (401) sauf celles-ci, qui acceptent `SessionUser` : `GET /api/me`, `GET /api/me/decisions`, `POST /api/me/decisions/{id}/contest`, `DELETE /api/session`. `tests/test_suspended.py` vérifie chaque route de l'API : partout ailleurs, il reçoit la même réponse qu'un visiteur.

- `GET /api/me/decisions` : les décisions qui me visent, les plus récentes d'abord, sans le nom de qui les a prises, chacune avec sa contestation (`contest`, ou `null`).
- `POST /api/me/decisions/{id}/contest` avec `{"body": "…"}` (10 à 2 000 caractères, espaces autour retirés) : 201. 404 si la décision ne me vise pas ou ne se conteste pas ; 409 si elle est déjà contestée.
- `GET /api/moderation/contests?status=open|answered` (capacité `moderate`) : en attente (les plus anciennes d'abord) ou traitées. `decided_by_me` signale une décision prise par la personne qui lit, pour qu'une autre relise si possible.
- `POST /api/moderation/contests/{id}/answer` avec `{"outcome": "upheld" | "lifted", "answer": "…"}` : 409 si déjà répondu, 403 sur un compte de rang égal ou supérieur. `lifted` lève la mesure si elle tient encore (`unhide`, `reinstate` ou `restore_reporting` au journal), puis `answer_contest` va au journal. La personne reçoit la réponse par mail.

### Le journal

`GET /api/moderation/journal`, filtrable par `action`, `actor_id`, `target_user_id` : qui, quoi, sur quoi, quand, pourquoi, le plus récent d'abord. Une action sur un serveur donne `target_server_id` et son nom actuel, `target_server_name`. Aucune route ne le modifie ni ne l'efface.

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
| Écrire une histoire | 30 créations en 1 heure, et 30 brouillons à la fois, par compte | 429, ou 409 pour les brouillons |
| Publier une histoire | 10 en 1 jour, par compte | 429 |
| Signaler | 10 en 1 heure, par compte | 429 |
| Taille d'une requête | 1 Mo, pour toute l'API (Caddy) | 413 |

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
- 403 si l'adresse n'est pas encore vérifiée. Seulement quand le mot de passe est bon, pour ne rien révéler à un inconnu. Un compte suspendu, lui, se connecte : voir « Contester une décision » ;
- 429.

### Se déconnecter

`DELETE /api/session`

Réponse 204, toujours, même sans session : le cookie est effacé et la session supprimée.

### Mon compte

`GET /api/me`

Réponse 200 :

```json
{"email": "toi@example.com", "role": "moderator", "created_at": "2026-11-23T10:00:00Z",
 "capabilities": ["ban", "moderate", "see_hidden", "see_owner"],
 "suspended": false, "suspended_until": null}
```

`suspended` : le compte est suspendu, jusqu'à `suspended_until` (vide : définitivement). Le site ne lui montre alors que sa suspension, de quoi la contester, et les pages légales.

`capabilities` : ce que la personne peut faire en plus d'un joueur, pour que le site montre les bons boutons (vide pour un joueur). Chaque route revérifie de son côté. La liste et ce que chaque rôle reçoit sont dans `accounts/roles.py` et `docs/permissions.md`.

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

Réponse 204. Le compte, ses personnages, leurs lieux, ses histoires, ses sessions et ses liens en cours sont supprimés, ainsi que les traces de son adresse dans les limites contre les abus. Les signalements restent, sans lien vers lui. Le cookie est effacé.

Erreurs : 401, 403 si le mot de passe est faux.

## Plus tard

Après ce contrat :

- l'export de ses données ;
- « Qui traîne ici ? » : les lieux d'un serveur et leurs habitués ;
- les histoires ;
