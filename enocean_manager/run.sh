#!/usr/bin/with-contenv bashio
set -euo pipefail

SERIAL_PORT="$(bashio::config 'serial_port')"
JSON_DIR="$(bashio::config 'json_dir')"

SERIAL_PORT="${SERIAL_PORT:-/dev/ttyUSB0}"
JSON_DIR="${JSON_DIR:-/data/profile_json}"

export SERIAL_PORT
export EEP_JSON_DIR="$JSON_DIR"

# Prépare le dossier persistant et copie les profils fournis au premier démarrage
mkdir -p "$EEP_JSON_DIR"
if [ -d "/opt/enocean_manager/app/profile_json" ]; then
  cp -rn /opt/enocean_manager/app/profile_json/* "$EEP_JSON_DIR"/ 2>/dev/null || true
fi

bashio::log.info "SERIAL_PORT=$SERIAL_PORT"
bashio::log.info "EEP_JSON_DIR=$EEP_JSON_DIR"

# Lancement de l'API Flask via gunicorn (Ingress écoute en interne sur 8099)
exec /opt/venv/bin/gunicorn -w 1 -b 0.0.0.0:${PORT:-8099} app:app
