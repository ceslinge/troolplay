# Sécurité

La relecture du site suivant le [Top 10 de l'OWASP](https://owasp.org/Top10/) (#56, novembre 2026). Pour chaque risque : ce qui protège le site, et ce qui reste à faire.

## A01 · Contrôle d'accès

- Chaque route vérifie la capacité (`require(Capability.X)`) ou la propriété ; jamais un nom de rôle.
- **`docs/permissions.md` est la spécification** : `tests/test_permissions_doc.py` lit son tableau et, pour chaque action et chaque rôle, essaie vraiment contre l'API. Document et code ne peuvent pas diverger.
- On n'agit que sur un rang inférieur au sien (`outranks`) ; le dernier admin reste admin.
- Un compte suspendu n'atteint que quatre routes (`SessionUser`) ; `tests/test_suspended.py` vérifie toutes les autres.
- Le contenu d'un autre (brouillon, contestation, demande à l'équipe) répond 404, pas 403 : on ne confirme pas qu'il existe.
- Aucune réponse publique ne contient de `user_id` (décision 6).

## A02 · Cryptographie

- Mots de passe : Argon2id (`pwdlib`). Jetons de session et de mail : 32 octets aléatoires, gardés en base sous forme d'empreinte SHA-256 seulement.
- HTTPS partout (Caddy, certificat automatique), HSTS d'un an, cookies `Secure` en production.

## A03 · Injection

- SQL : uniquement par SQLAlchemy, paramétré ; aucune requête écrite à la main avec une saisie.
- HTML : React échappe tout. Le seul HTML brut est celui des pages légales, tiré du dépôt au moment du build.
- Content-Security-Policy stricte : scripts, styles, polices et images du site seulement ; aucune balise `<style>` ou `<script>` en ligne (seuls les attributs `style="…"` des composants sont permis). Vérifié dans Chromium à travers le Caddy de production : aucune violation sur les pages du site, une balise `<style>` injectée est bloquée.

## A04 · Conception

- Limites de débit (`throttle`) : inscription, mails de vérification et de mot de passe, connexions ratées, histoires, publication, signalements, demandes à l'équipe, et depuis cette passe, **création de personnage** (10 par jour : supprimer et recréer en boucle inondait l'accueil).
- Plafonds : 10 personnages, 30 brouillons, 3 lieux, 3 demandes ouvertes, une contestation par décision (garantie en base).
- Corps de requête limité à 1 Mo par Caddy ; chaque champ texte a sa longueur maximale, et un champ obligatoire refuse des espaces seuls (`tests/test_text_fields.py`).

## A05 · Configuration

- En-têtes : HSTS, CSP, `X-Frame-Options: DENY` et `frame-ancestors 'none'`, `X-Content-Type-Options`, `Referrer-Policy`, `Permissions-Policy`, et depuis cette passe `Cross-Origin-Opener-Policy` et `Cross-Origin-Resource-Policy`. L'en-tête `Server` est retiré.
- **Corrigé :** la documentation interactive de l'API (`/api/docs`, `/api/openapi.json`) était publique en production. Elle est éteinte, sauf en local avec `API_DOCS=true` (`tests/test_api_docs.py`).
- Seul Caddy est exposé ; l'API et la base ne le sont pas. Les erreurs 500 ne montrent aucune trace.

## A06 · Composants vulnérables

- `npm audit` et `pip-audit` : aucune vulnérabilité connue (novembre 2026).
- **Ajouté :** Dependabot (`.github/dependabot.yml`) surveille npm, uv, les actions GitHub et les images Docker, chaque semaine.

## A07 · Authentification

- Connexion : même réponse et même durée pour une adresse inconnue ou un mauvais mot de passe ; limite par adresse et par IP.
- Nouvelle session à chaque connexion ; déconnexion effacée côté serveur ; changer ou réinitialiser son mot de passe ferme les autres sessions.
- Liens de vérification et de réinitialisation : expirent, ne servent qu'une fois.
- CSRF : cookies `SameSite=Lax`, et toute requête qui modifie quelque chose doit venir du site (en-tête `Origin` vérifié).

## A08 · Intégrité

- Dépendances verrouillées (`uv.lock`, `package-lock.json`), installées telles quelles en CI (`uv sync --locked`, `npm ci`).

## A09 · Journaux et alertes

- Le journal de modération garde chaque geste de l'équipe. Les journaux techniques et les alertes : #61.

## A10 · Requêtes côté serveur (SSRF)

- Le serveur n'appelle aucune adresse fournie par un membre. À revoir si les portraits passent un jour par un site extérieur.

## Reste à faire, hors du code

- Dans les réglages GitHub : alertes Dependabot, analyse des secrets et protection à l'envoi, signalement privé des vulnérabilités.
- Une fois le domaine choisi : `includeSubDomains`, voire `preload`, sur HSTS.
- Décider d'un `SECURITY.md` (comment signaler une faille).
- Épingler les actions GitHub par empreinte plutôt que par version, si l'on veut aller plus loin (Dependabot les tiendra à jour).
