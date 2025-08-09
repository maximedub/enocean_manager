# Dockerfile (multi-arch via BUILD_FROM, conforme add-ons)
ARG BUILD_FROM
FROM $BUILD_FROM

# Paquets système (python, pip, git, build tools si besoin de wheels natifs)
RUN apk add --no-cache \
      python3 py3-pip git \
      gcc musl-dev libffi-dev libxml2-dev libxslt-dev

# Venv pour éviter PEP 668
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Dépendances Python
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir \
      --extra-index-url https://wheels.home-assistant.io/musllinux-index/ \
      -r /tmp/requirements.txt

# Code de l’add-on
# (Présume que tout le code est à la racine du contexte)
COPY . /opt/enocean_manager
ENV PYTHONPATH="/opt/enocean_manager:${PYTHONPATH}"

# Script d’entrée
COPY run.sh /run.sh
RUN chmod +x /run.sh

# Home Assistant s’occupe du démarrage (s6-overlay)
CMD [ "/run.sh" ]
