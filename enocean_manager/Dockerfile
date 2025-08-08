# Base Home Assistant (PEP 668) + virtualenv pour autoriser pip
ARG BUILD_FROM=ghcr.io/home-assistant/aarch64-base:latest
FROM ${BUILD_FROM}

# Outils nécessaires
RUN apk add --no-cache python3 py3-pip gcc musl-dev libffi-dev

# Log de debug pour vérifier la base dans le build log
RUN echo "BASE_IMAGE=ghcr.io/home-assistant/aarch64-base:latest"

# Créer un venv pour contourner PEP 668
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:${PATH}"

# Dépendances Python dans le venv
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Code de l’add-on (contexte = dossier enocean_manager/)
COPY . /opt/enocean_manager

# Copier les profils JSON en volume persistant (si présents dans le repo)
RUN mkdir -p /data/profile_json && \
    if [ -d "/opt/enocean_manager/app/profile_json" ]; then \
      cp -r /opt/enocean_manager/app/profile_json/* /data/profile_json/ || true; \
    fi

# Script d’entrée
COPY run.sh /run.sh
RUN chmod +x /run.sh

CMD [ "/run.sh" ]
