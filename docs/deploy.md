# Déployer

La production tient dans `compose.prod.yaml` : Postgres, l'API et Caddy, qui sert le site en HTTPS et transmet `/api` à l'API (décision 20). Seuls les ports 80 et 443 sont ouverts au monde ; la base n'a aucun port publié.

Au démarrage, l'API met la base à jour (`alembic upgrade head`) et ajoute les serveurs officiels qui manquent. Il n'y a rien d'autre à lancer à la main.

## Préparer le serveur, une fois

Un VPS sous Debian, avec une adresse IP publique. Les commandes sont à lancer sur le serveur, sauf mention contraire.

1. **Le nom de domaine** : chez le registraire, un enregistrement `A` (et `AAAA` si le serveur a une IPv6) qui pointe le domaine vers l'IP du serveur.

2. **Se connecter par clé.** Depuis ton ordinateur, si tu n'as pas encore de clé : `ssh-keygen -t ed25519`. Ajoute la clé publique (`~/.ssh/id_ed25519.pub`) à la création du VPS, ou ensuite avec `ssh-copy-id root@<ip>`.

3. **Un compte à toi, puis plus de root ni de mot de passe :**
   ```
   adduser <toi>
   usermod -aG sudo <toi>
   mkdir -p /home/<toi>/.ssh && cp /root/.ssh/authorized_keys /home/<toi>/.ssh/
   chown -R <toi>:<toi> /home/<toi>/.ssh
   ```
   Vérifie dans un **autre terminal** que `ssh <toi>@<ip>` fonctionne, puis dans `/etc/ssh/sshd_config.d/durcir.conf` :
   ```
   PermitRootLogin no
   PasswordAuthentication no
   KbdInteractiveAuthentication no
   ```
   et `sudo systemctl reload ssh`. Garde la première session ouverte tant que la nouvelle n'a pas marché.

4. **Le pare-feu :**
   ```
   sudo apt install ufw
   sudo ufw allow OpenSSH
   sudo ufw allow 80,443/tcp
   sudo ufw allow 443/udp
   sudo ufw enable
   ```
   Docker contourne ufw pour les ports qu'il publie : c'est pourquoi `compose.prod.yaml` ne publie que 80 et 443, et jamais la base.

5. **Les mises à jour de sécurité automatiques :** `sudo apt install unattended-upgrades`.

6. **Docker**, depuis son dépôt officiel (docs.docker.com/engine/install/debian), puis `sudo usermod -aG docker <toi>` et une reconnexion.

## Mettre le site en ligne

```
git clone https://github.com/ceslinge/troolplay.git
cd troolplay
cp .env.example .env
```

Dans `.env` : un mot de passe de base long et aléatoire (`openssl rand -base64 32`), et `SITE_DOMAIN` avec le domaine, sans `https://`. Puis :

```
docker compose -f compose.prod.yaml up -d --build
docker compose -f compose.prod.yaml logs -f
```

Caddy obtient le certificat HTTPS tout seul, dès que le domaine pointe vers le serveur. Le site doit répondre sur `https://<domaine>`, et `https://<domaine>/api/health` donner `{"status":"ok"}`.

Le premier admin, une fois ton compte créé sur le site :

```
docker compose -f compose.prod.yaml exec backend python -m backend.admin promote <ton-adresse> --role admin
```

## Les emails

Sans `SMTP_HOST`, rien ne part : les emails s'affichent dans `docker compose -f compose.prod.yaml logs backend`. Pratique pour un tout premier essai, pas pour de vrais joueurs.

Avec la boîte email fournie avec le domaine chez OVH (MX Plan), dans `.env` :

```
SMTP_HOST=ssl0.ovh.net
SMTP_PORT=465
SMTP_USER=contact@<domaine>
SMTP_PASSWORD=<le mot de passe de la boîte>
```

Puis `docker compose -f compose.prod.yaml up -d` pour en tenir compte. Le mot de passe ne vit que dans `.env`, sur le serveur, jamais dans le dépôt.

Pour que les emails n'arrivent pas dans les indésirables, le domaine doit dire qui a le droit d'envoyer en son nom. Dans la zone DNS chez OVH :

- **SPF** : un enregistrement TXT `v=spf1 include:mx.ovh.com ~all` (OVH le propose tout fait).
- **DKIM** : à activer dans l'espace client OVH, rubrique de la boîte email ; OVH ajoute les enregistrements.
- **DMARC** : un enregistrement TXT sur `_dmarc.<domaine>` : `v=DMARC1; p=none; rua=mailto:contact@<domaine>`. On passera à `p=quarantine` une fois sûrs que tout passe (#59).

Pour vérifier : s'inscrire avec une vraie adresse (Gmail, Outlook…), et regarder que l'email arrive en boîte de réception. Dans Gmail, « Afficher l'original » indique si SPF, DKIM et DMARC sont passés.

## Mettre à jour

```
git pull
docker compose -f compose.prod.yaml up -d --build
```

## Les journaux

- Caddy écrit les accès dans son volume (`/data/logs/access.log`) et les efface au bout de 30 jours, comme promis dans la page de confidentialité.
- L'API ne tient pas de journal d'accès. Les journaux des conteneurs tournent à 3 fichiers de 10 Mo.

## Essayer la production sur son ordinateur

Avec un fichier d'environnement à part (par exemple `SITE_DOMAIN=localhost`, `HTTP_PORT=8080`, `HTTPS_PORT=8443`) et un nom de projet distinct, pour ne pas toucher à la base de développement :

```
docker compose -p troolplay-essai --env-file <fichier> -f compose.prod.yaml up -d --build
docker compose -p troolplay-essai --env-file <fichier> -f compose.prod.yaml down -v
```

Le site répond alors sur `https://localhost:8443`, avec un certificat local que le navigateur signale.
