# Utilise l’ARG BUILD_FROM fourni par le builder (défini via build.json)
ARG BUILD_FROM=ghcr.io/hassio-addons/base-python:14.3.5
FROM $BUILD_FROM

# --- File system ---
# Copie l’application
COPY app /app

# --- Dépendances Python ---
# Assure la présence de python/pip même si l’image BASE n’est pas "base-python"
# (ex: si le builder retombe sur ghcr.io/home-assistant/<arch>-base)
RUN if ! command -v python3 >/dev/null 2>&1; then \
      apk add --no-cache python3 py3-pip; \
    fi \
 && python3 -m pip install --no-cache-dir -r /app/requirements.txt

# --- Entrypoint ---
# Script de démarrage (s6-overlay + bashio)
COPY run.sh /run.sh
RUN chmod a+x /run.sh

# L’add-on expose l’API FastAPI (uvicorn)
CMD [ "/run.sh" ]
