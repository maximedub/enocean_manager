#!/usr/bin/env bash
set -euo pipefail
OPTIONS_FILE="/data/options.json"
SERIAL_PORT=$(jq -r '.serial_port // "/dev/ttyUSB0"' "$OPTIONS_FILE")
JSON_DIR=$(jq -r '.json_dir // "/data/profile_json"' "$OPTIONS_FILE")
export EEP_JSON_DIR="$JSON_DIR"
echo "[EnOcean Manager] SERIAL_PORT=$SERIAL_PORT"
echo "[EnOcean Manager] EEP_JSON_DIR=$EEP_JSON_DIR"
PY=/opt/venv/bin/python3
[ -x "$PY" ] || PY=python3
exec "$PY" -m enocean_manager.app.main --serial-port "$SERIAL_PORT"
