# Les outils de Postgres (pg_dump, pg_restore) et rclone pour la copie hors du serveur.
FROM postgres:18-alpine
RUN apk add --no-cache rclone \
  # Tout se règle par l'environnement : un fichier vide évite que rclone le réclame à chaque fois.
  && mkdir -p /root/.config/rclone && touch /root/.config/rclone/rclone.conf
COPY --chmod=755 deploy/backup.sh /usr/local/bin/backup.sh
COPY --chmod=755 deploy/restore.sh /usr/local/bin/restore.sh
COPY --chmod=755 deploy/nightly.sh /usr/local/bin/nightly.sh
CMD ["nightly.sh"]
