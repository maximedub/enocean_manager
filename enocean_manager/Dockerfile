# Base officielle pour add-ons Home Assistant (Alpine + s6)
ARG BUILD_FROM=ghcr.io/hassio-addons/base:16.2.3
FROM ${BUILD_FROM}

ENV LANG=C.UTF-8 \
    PYTHONUNBUFFERED=1

# Assure pip présent (au cas où) + build deps minimales
# (la base a souvent python3/pip déjà, mais c'est safe)
RUN apk add --no-cache python3 py3-pip gcc musl-dev libffi-dev

# Installer les dépendances Python
COPY requirements.txt /tmp/requirements.txt
RUN python3 -m pip install --no-cache-dir -r /tmp/requirements.txt

# Copier le code de l’application (contexte = dossier enocean_manager/)
COPY . /opt/enocean_manager

# Préparer /data/profile_json (persistant) et y copier les profils du repo si présents
RUN mkdir -p /data/profile_json && \
    if [ -d "/opt/enocean_manager/app/profile_json" ]; then \
      cp -r /opt/enocean_manager/app/profile_json/* /data/profile_json/ || true; \
    fi

# Script d’entrée
COPY run.sh /run.sh
RUN chmod a+x /run.sh

CMD [ "/run.sh" ]
