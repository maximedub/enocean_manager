# Dockerfile de l’add-on Home Assistant EnOcean
# ----------------------------------------------
# - Base HA officielle (Alpine + s6 overlay)
# - venv Python pour éviter PEP 668
# - Installation des dépendances depuis requirements.txt
# - Copie du code puis exécution via run.sh

ARG BUILD_FROM
FROM $BUILD_FROM

# ---- Paquets systèmes utiles (Alpine) ----
# gcc/musl-dev/libffi-dev utiles pour compiler certaines roues le cas échéant
RUN apk add --no-cache \
      python3 \
      py3-pip \
      gcc \
      musl-dev \
      libffi-dev

# ---- Variables d'environnement utiles ----
# IMPORTANT : chaque var doit respecter la forme NOM=valeur
ENV PYTHONDONTWRITEBYTECODE=1 \  # Évite la création des .pyc
    PYTHONUNBUFFERED=1 \         # Logs non bufferisés
    PIP_DISABLE_PIP_VERSION_CHECK=1

# ---- Environnement virtuel Python (évite PEP 668) ----
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:${PATH}"

# ---- Dépendances Python dans le venv ----
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --upgrade pip setuptools wheel \
 && pip install --no-cache-dir -r /tmp/requirements.txt

# ---- Code de l’add-on (contexte = dossier enocean_manager/) ----
# On copie le dossier entier de l’app Python dans /opt/enocean_manager
COPY ../enocean_manager /opt/enocean_manager

# ---- Script d’entrée ----
COPY run.sh /run.sh
RUN chmod a+x /run.sh

# ---- Commande de démarrage ----
CMD [ "/run.sh" ]
