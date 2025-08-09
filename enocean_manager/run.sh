#!/usr/bin/with-contenv bashio
# ^ utilise l’environnement s6-overlay + bashio fourni par la base HA

set -euo pipefail                                   # Mode strict : stop sur erreur
IFS=$'\n\t'

# --- Chemins et options HA ---
OPTIONS_FILE="/data/options.json"                   # Fichier d’options injecté par le Supervisor

# Lit les options utilisateur (avec valeurs par défaut)
SERIAL_PORT=$(jq -r '.serial_port // "/dev/ttyUSB0"' "$OPTIONS_FILE")   # Port série du dongle
JSON_DIR=$(jq -r '.json_dir // "/data/profile_json"' "$OPTIONS_FILE")    # Dossier des profils EEP JSON

# --- Expose le chemin pour l’app Python ---
export EEP_JSON_DIR="$JSON_DIR"                     # eep.py le lit pour trouver les .json

# --- Logs de démarrage ---
bashio::log.info "EnOcean Manager - SERIAL_PORT=${SERIAL_PORT}"
bashio::log.info "EnOcean Manager - EEP_JSON_DIR=${EEP_JSON_DIR}"

# --- S’assure que le dossier des profils existe ---
mkdir -p "$EEP_JSON_DIR"                            # Crée le dossier si manquant

# --- Lance l’application Python via le venv ---
# On appelle explicitement le Python du venv pour éviter toute ambiguïté.
exec /opt/venv/bin/python -m enocean_manager.app.main --serial-port "$SERIAL_PORT"
#                      ^ module main de ton app, qui importe communicator/eep/pairing
