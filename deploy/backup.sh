#!/bin/sh
# Une sauvegarde de la base, maintenant.
#   docker compose -f compose.prod.yaml exec backup backup.sh
#
# Sur le serveur, dans ./backups : les 7 derniers jours, et un dimanche par semaine sur 4 semaines.
# Hors du serveur, si S3_BUCKET est réglé : une copie de chacune, gardée 35 jours.
set -eu

DIR=/backups
mkdir -p "$DIR/jour" "$DIR/semaine"

day=$(date -u +%Y-%m-%d)
file="$DIR/jour/troolplay-$day.dump"

# Format « custom » de Postgres : compressé, et restaurable table par table au besoin.
pg_dump --host=db --username="$POSTGRES_USER" --dbname="$POSTGRES_DB" \
  --format=custom --file="$file.partiel"
# Un fichier qu'on ne sait pas relire n'est pas une sauvegarde.
pg_restore --list "$file.partiel" > /dev/null
mv "$file.partiel" "$file"
echo "Sauvegarde : $file ($(du -h "$file" | cut -f1))"

if [ "$(date -u +%u)" = 7 ]; then
  cp "$file" "$DIR/semaine/"
fi

# On ne garde que les plus récentes.
ls -1t "$DIR"/jour/*.dump | tail -n +8 | xargs -r rm --
ls -1t "$DIR"/semaine/*.dump 2>/dev/null | tail -n +5 | xargs -r rm --

if [ -n "${S3_BUCKET:-}" ]; then
  rclone copy "$file" "horsite:$S3_BUCKET/"
  rclone delete --min-age 35d "horsite:$S3_BUCKET/"
  echo "Copie hors du serveur : $S3_BUCKET"
else
  echo "Pas de copie hors du serveur : S3_BUCKET n'est pas réglé."
fi
