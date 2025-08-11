# Image de base définie par le builder (override via build.json)
ARG BUILD_FROM=ghcr.io/home-assistant/amd64-base-python:3.13-alpine3.21
FROM $BUILD_FROM

# Copier l’application
COPY app /app

# Installer les dépendances Python (pip est présent dans *-base-python)
RUN python3 -m pip install --no-cache-dir -r /app/requirements.txt

# Script de démarrage
COPY run.sh /run.sh
RUN chmod a+x /run.sh

# L’add-on expose l’API FastAPI (uvicorn)
CMD [ "/run.sh" ]
