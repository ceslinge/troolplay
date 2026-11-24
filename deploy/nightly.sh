#!/bin/sh
# Le service de sauvegarde : une sauvegarde chaque nuit à 3 h 30 (UTC), sans fin.
set -u

AT=$((3 * 3600 + 30 * 60))

while true; do
  now=$(($(date -u +%s) % 86400))
  wait=$(((AT - now + 86400) % 86400))
  [ "$wait" -eq 0 ] && wait=86400
  sleep "$wait"
  # Une nuit ratée ne doit pas arrêter les suivantes : le message reste dans les journaux.
  backup.sh || echo "ÉCHEC de la sauvegarde du $(date -u +%Y-%m-%d)" >&2
done
