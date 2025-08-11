# Image de base pour add-ons Python (avec s6-overlay)
ARG BUILD_FROM=ghcr.io/hassio-addons/base-python:14.3.5
FROM $BUILD_FROM

# Copier l’application dans l’image
COPY app /app

# Installer les dépendances Python
RUN pip install --no-cache-dir -r /app/requirements.txt

# Script de démarrage
COPY run.sh /run.sh
RUN chmod a+x /run.sh

# L’add-on expose l’API/serveur web FastAPI (uvicorn)
CMD [ "/run.sh" ]
