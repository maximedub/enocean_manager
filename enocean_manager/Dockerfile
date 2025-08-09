# Utilise l’image de base Home Assistant (arch remplacée par le Supervisor)
ARG BUILD_FROM
FROM $BUILD_FROM

# Un runtime Python propre
ENV PYTHONUNBUFFERED=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Paquets système (git requis pour pip install depuis un dépôt Git)
RUN apk add --no-cache \
    python3 py3-pip \
    git \
    gcc musl-dev libffi-dev libxml2-dev libxslt-dev

# Environnement virtuel
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:${PATH}"

# Dépendances Python
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir \
      --extra-index-url https://wheels.home-assistant.io/musllinux-index/ \
      -r /tmp/requirements.txt

# Code de l’addon
WORKDIR /opt/enocean_manager
COPY . /opt/enocean_manager
RUN chmod +x /opt/enocean_manager/run.sh

# Point d’entrée (s6 overlay appelera ce script)
CMD [ "/opt/enocean_manager/run.sh" ]
