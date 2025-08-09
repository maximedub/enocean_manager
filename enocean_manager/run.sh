#!/usr/bin/with-contenv bashio
set -euo pipefail

SERIAL_PORT="$(bashio::config 'serial_port')"
JSON_DIR="$(bashio::config 'json_dir')"

# Valeurs par défaut si non définies
SERIAL_PORT="${SERIAL_PORT:-/dev/ttyUSB0}"
JSON_DIR="${JSON_DIR:-/data/profile_json}"

export EEP_JSON_DIR="$JSON_DIR"
export PYTHONPATH="/opt/enocean_manager:${PYTHONPATH:-}"

# Prépare le dossier persistant et copie les profils fournis par le repo au premier démarrage
mkdir -p "$EEP_JSON_DIR"
if [ -d "/opt/enocean_manager/app/profile_json" ]; then
  cp -rn /opt/enocean_manager/app/profile_json/* "$EEP_JSON_DIR"/ 2>/dev/null || true
fi

bashio::log.info "SERIAL_PORT=$SERIAL_PORT"
bashio::log.info "EEP_JSON_DIR=$EEP_JSON_DIR"

# Démarre l'application
exec python3 -m enocean_manager.app.main --serial-port "$SERIAL_PORT"
