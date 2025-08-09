# Image de base fournie par Home Assistant (le Supervisor injecte BUILD_FROM)
ARG BUILD_FROM
FROM $BUILD_FROM

# ---- Paquets système utiles ----
RUN apk add --no-cache \
      python3 \
      py3-pip \
      gcc \
      musl-dev \
      libffi-dev

# ---- Venv Python pour éviter PEP 668 (environment externally managed) ----
RUN python3 -m venv /opt/venv

# IMPORTANT : une variable par ligne, SANS commentaires inline
ENV PATH="/opt/venv/bin:${PATH}"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# ---- Dépendances Python (via l’index musllinux de HA + PyPI) ----
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir \
      --extra-index-url https://wheels.home-assistant.io/musllinux-index/ \
      -r /tmp/requirements.txt

# ---- Code de l’add-on (contexte = dossier enocean_manager/) ----
# Adapte ce chemin si besoin : on copie le dossier de ton app dans /opt/enocean_manager
COPY ../enocean_manager /opt/enocean_manager

# ---- Script d’entrée ----
COPY run.sh /run.sh
RUN chmod a+x /run.sh

# ---- Démarrage ----
CMD [ "/run.sh" ]
