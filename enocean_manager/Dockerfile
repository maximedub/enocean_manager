ARG BUILD_FROM=ghcr.io/home-assistant/aarch64-base:latest
FROM $BUILD_FROM

# OS deps (Python, pip, git, compilos pour lxml, etc.)
RUN apk add --no-cache \
    python3 py3-pip git \
    gcc musl-dev libffi-dev libxml2-dev libxslt-dev

# Venv pour éviter PEP 668
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Dépendances Python (index musllinux de Home Assistant pour wheels compatibles)
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir \
    --extra-index-url https://wheels.home-assistant.io/musllinux-index/ \
    -r /tmp/requirements.txt

# Code de l’add-on (assure-toi que le dossier source contient le package enocean_manager/)
WORKDIR /opt/enocean_manager
COPY . /opt/enocean_manager

# Variables utiles
ENV EEP_JSON_DIR="/data/profile_json"

# Entrée (s6 du base image lancera /run.sh)
COPY run.sh /run.sh
RUN chmod +x /run.sh
