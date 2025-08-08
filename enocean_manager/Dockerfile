# Base officielle pour add-ons Home Assistant (gère s6, jq, /data, etc.)
ARG BUILD_FROM=ghcr.io/hassio-addons/base:16.2.3
FROM ${BUILD_FROM}

# Variables d’environnement basiques
ENV LANG=C.UTF-8 \
    PYTHONUNBUFFERED=1

# Installer les dépendances Python de l’add-on
COPY requirements.txt /tmp/requirements.txt
RUN python3 -m pip install --no-cache-dir -r /tmp/requirements.txt

# Copier le code de l’application dans l’image
COPY ../enocean_manager /opt/enocean_manager

# Préparer /data/profile_json (persistant) et y copier les profils du repo si présents
RUN mkdir -p /data/profile_json && \
    if [ -d "/opt/enocean_manager/app/profile_json" ]; then \
      cp -r /opt/enocean_manager/app/profile_json/* /data/profile_json/ || true; \
    fi

# Script d’entrée de l’add-on
COPY run.sh /run.sh
RUN chmod a+x /run.sh

# L’add-on démarre via run.sh (lit /data/options.json, exporte EEP_JSON_DIR)
CMD [ "/run.sh" ]
