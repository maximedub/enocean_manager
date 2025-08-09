#!/usr/bin/with-contenv bashio
set -euo pipefail

SERIAL_PORT="$(bashio::config 'serial_port' || echo /dev/ttyUSB0)"
JSON_DIR="$(bashio::config 'json_dir' || echo /data/profile_json)"

export EEP_JSON_DIR="$JSON_DIR"
export PYTHONPATH="/opt/enocean_manager:${PYTHONPATH:-}"

mkdir -p "$EEP_JSON_DIR"
if [ -d "/opt/enocean_manager/enocean_manager/app/profile_json" ]; then
  cp -rn /opt/enocean_manager/enocean_manager/app/profile_json/* "$EEP_JSON_DIR"/ 2>/dev/null || true
fi

bashio::log.info "SERIAL_PORT=$SERIAL_PORT"
bashio::log.info "EEP_JSON_DIR=$EEP_JSON_DIR"

# Démarre l'app Flask via gunicorn (pour Ingress)
exec /opt/venv/bin/gunicorn -w 1 -b 0.0.0.0:8099 enocean_manager.app:app
