#!/usr/bin/env bash
# Script d’entrée : lit les options, exporte EEP_JSON_DIR, lance le Python du venv
set -euo pipefail                                   # stop on error, unset, pipefail

OPTIONS_FILE="/data/options.json"                   # options injectées par Supervisor
SERIAL_PORT=$(jq -r '.serial_port // "/dev/ttyUSB0"' "$OPTIONS_FILE")
JSON_DIR=$(jq -r '.json_dir // "/data/profile_json"' "$OPTIONS_FILE")

export EEP_JSON_DIR="$JSON_DIR"                     # exposition à l’app

echo "[EnOcean Manager] SERIAL_PORT=$SERIAL_PORT"
echo "[EnOcean Manager] EEP_JSON_DIR=$EEP_JSON_DIR"

# Utiliser le Python du venv (fallback sur python3 si jamais absent)
PY="/opt/venv/bin/python3"
[ -x "$PY" ] || PY="python3"

exec "$PY" -m enocean_manager.app.main --serial-port "$SERIAL_PORT"
