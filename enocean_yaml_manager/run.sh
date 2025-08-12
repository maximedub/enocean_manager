#!/usr/bin/with-contenv bashio
# Lance l'API FastAPI et exporte les 4 chemins des YAML.
set -euo pipefail

AUTO_OUTPUT_PATH="$(bashio::config 'auto_output_path')"
AUTO_BACKUP_PATH="$(bashio::config 'auto_backup_path')"
CONFIG_OUTPUT_PATH="$(bashio::config 'config_output_path')"
CONFIG_BACKUP_PATH="$(bashio::config 'config_backup_path')"

export AUTO_OUTPUT_PATH
export AUTO_BACKUP_PATH
export CONFIG_OUTPUT_PATH
export CONFIG_BACKUP_PATH

# Crée les répertoires/fichiers si nécessaire
mkdir -p "$(dirname "$AUTO_OUTPUT_PATH")" "$(dirname "$CONFIG_OUTPUT_PATH")"
mkdir -p "$(dirname "$AUTO_BACKUP_PATH")" "$(dirname "$CONFIG_BACKUP_PATH")"
touch "$AUTO_OUTPUT_PATH" "$CONFIG_OUTPUT_PATH"

# Démarre le serveur FastAPI (uvicorn)
exec python -m uvicorn app.main:app --host 0.0.0.0 --port 9123
