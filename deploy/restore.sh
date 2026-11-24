#!/bin/sh
# Remet la base dans l'état d'une sauvegarde. Tout ce qui a été écrit depuis est perdu.
#   docker compose -f compose.prod.yaml stop backend
#   docker compose -f compose.prod.yaml exec backup restore.sh /backups/jour/troolplay-AAAA-MM-JJ.dump
#   docker compose -f compose.prod.yaml start backend
#
# Une sauvegarde hors du serveur se rapatrie d'abord :
#   docker compose -f compose.prod.yaml exec backup rclone copy horsite:<bucket>/troolplay-AAAA-MM-JJ.dump /backups/
set -eu

file=${1:?Quelle sauvegarde ? Par exemple /backups/jour/troolplay-2026-11-24.dump}
[ -f "$file" ] || { echo "Pas de fichier $file" >&2; exit 1; }
pg_restore --list "$file" > /dev/null

echo "La base $POSTGRES_DB va être remplacée par $file."
if [ "${2:-}" != "--oui" ]; then
  printf "Écris « oui » pour continuer : "
  read -r answer
  [ "$answer" = oui ] || { echo "Rien n'a changé."; exit 1; }
fi

# Une transaction : si quoi que ce soit échoue, la base reste telle qu'elle était.
pg_restore --host=db --username="$POSTGRES_USER" --dbname="$POSTGRES_DB" \
  --clean --if-exists --no-owner --single-transaction "$file"
echo "Base restaurée depuis $file. Relance l'API : docker compose -f compose.prod.yaml start backend"
