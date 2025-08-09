# Base HA (le Supervisor injecte BUILD_FROM)
ARG BUILD_FROM
FROM $BUILD_FROM

# Variables d'environnement sûres
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Dépendances système utiles pour lxml, etc.
RUN apk add --no-cache \
    python3 py3-pip \
    gcc musl-dev libffi-dev \
    libxml2-dev libxslt-dev \
    git

# Crée un venv pour installer les paquets Python
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:${PATH}"

# Dépendances Python (avec index musllinux de HA)
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir \
      --extra-index-url https://wheels.home-assistant.io/musllinux-index/ \
      -r /tmp/requirements.txt

# Code de l’add-on (on reste DANS le dossier de l’add-on)
COPY app /opt/enocean_manager/app
COPY run.sh /run.sh
RUN chmod a+x /run.sh

# Assure la découverte du package au runtime
ENV PYTHONPATH="/opt/enocean_manager:${PYTHONPATH}"

# Entrypoint
CMD [ "/run.sh" ]
