#!/usr/bin/with-contenv bashio
# Lance l'API FastAPI et exporte les 4 chemins des YAML.
set -euo pipefail

# Récupère les options définies dans config.yaml (Supervisor)
AUTO_OUTPUT_PATH="$(bashio::config 'auto_output_path')"          # chemin auto.yaml
AUTO_BACKUP_PATH="$(bashio::config 'auto_backup_path')"          # backup auto.yaml
CONFIG_OUTPUT_PATH="$(bashio::config 'config_output_path')"      # chemin config.yaml
CONFIG_BACKUP_PATH="$(bashio::config 'config_backup_path')"      # backup config.yaml

# Exporte ces valeurs pour que l'app Python les lise via os.environ
export AUTO_OUTPUT_PATH
export AUTO_BACKUP_PATH
export CONFIG_OUTPUT_PATH
export CONFIG_BACKUP_PATH

# Crée les répertoires/fichiers si nécessaire
mkdir -p "$(dirname "$AUTO_OUTPUT_PATH")" "$(dirname "$CONFIG_OUTPUT_PATH")"
touch "$AUTO_OUTPUT_PATH" "$CONFIG_OUTPUT_PATH"

# Démarre le serveur FastAPI (uvicorn) — UI sur /ui
exec python -m uvicorn app.main:app --host 0.0.0.0 --port 9123
