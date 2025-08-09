# run.sh
#!/usr/bin/with-contenv bashio
set -e

# Ensure the EEP JSON dir exists in /data (persisted volume)
export EEP_JSON_DIR="${EEP_JSON_DIR:-/data/profile_json}"
mkdir -p "$EEP_JSON_DIR"

# Serial port from add-on options or default
export SERIAL_PORT="${SERIAL_PORT:-/dev/ttyUSB0}"

# Start the Flask app via Gunicorn (Ingress terminates TLS; 8099 is a good default)
exec /opt/venv/bin/gunicorn -b 0.0.0.0:8099 enocean_manager.app:app
