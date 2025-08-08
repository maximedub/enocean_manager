#!/usr/bin/env bash
# Script d’entrée : lit les options, exporte EEP_JSON_DIR, démarre l’app Python
set -euo pipefail                                  # Mode strict : stop en cas d’erreur

OPTIONS_FILE="/data/options.json"                 # Fichier des options HA (injecté par Supervisor)
SERIAL_PORT=$(jq -r '.serial_port // "/dev/ttyUSB0"' "$OPTIONS_FILE")  # Lit port série ou défaut
JSON_DIR=$(jq -r '.json_dir // "/data/profile_json"' "$OPTIONS_FILE")  # Lit json_dir ou défaut

export EEP_JSON_DIR="$JSON_DIR"                   # Expose le chemin aux modules Python

echo "[EnOcean Manager] SERIAL_PORT=$SERIAL_PORT"  # Log d’info au démarrage
echo "[EnOcean Manager] EEP_JSON_DIR=$EEP_JSON_DIR"

# Lance l’application Python (point d’entrée enocean_manager/app/main.py)
exec python3 -m enocean_manager.app.main --serial-port "$SERIAL_PORT"
