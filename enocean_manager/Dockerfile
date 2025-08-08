# ---- Base Home Assistant (gère s6-overlay, etc.) ----
ARG BUILD_FROM
FROM $BUILD_FROM

# ---- Métadonnées obligatoires pour HA ----
# io.hass.version est remplie automatiquement par le builder, mais on laisse l’étiquette type/arch
LABEL \
  io.hass.type="addon" \
  io.hass.arch="armhf|aarch64|i386|amd64"

# ---- Variables d'environnement utiles ----
ENV \
  PYTHONDONTWRITEBYTECODE=1 \        # Évite les .pyc
  PYTHONUNBUFFERED=1 \               # Logs non bufferisés
  PIP_NO_CACHE_DIR=1                 # Pas de cache pip
  PATH="/opt/venv/bin:${PATH}"       # Préfère le venv pour python/pip

# ---- Paquets système nécessaires ----
RUN \
  apk add --no-cache \
    python3 \                        # Interpréteur Python
    py3-pip \                        # pip pour Python (install initiale du venv)
    git \                            # requis pour "pip install" depuis GitHub
    jq \                             # parse /data/options.json dans run.sh
    gcc musl-dev libffi-dev          # toolchain si une wheel doit être compilée

# ---- Environnement Python isolé (PEP 668-safe) ----
RUN python3 -m venv /opt/venv        # Crée un venv pour éviter l'erreur "externally managed env"

# ---- Dépendances Python ----
COPY requirements.txt /tmp/requirements.txt   # Copie la liste de dépendances
RUN pip install --no-cache-dir -r /tmp/requirements.txt  # Installe via le venv (PATH déjà pointé)

# ---- Code de l’add-on (contexte = dossier racine du dépôt) ----
# On copie uniquement le dossier de l’app pour garder l’image propre.
COPY ../enocean_manager /opt/enocean_manager   # Code Python de l’app

# ---- Préparation des profils JSON persistants (/data) ----
# À l’installation, on amorce /data/profile_json avec le contenu du dépôt s’il existe.
RUN mkdir -p /data/profile_json && \
    if [ -d "/opt/enocean_manager/app/profile_json" ]; then \
      cp -r /opt/enocean_manager/app/profile_json/* /data/profile_json/ || true; \
    fi

# ---- Script d'entrée ----
COPY run.sh /run.sh                  # Script s6/cont-init-like minimal
RUN chmod a+x /run.sh                # Rendre exécutable

# ---- Point d'entrée de l’add-on ----
CMD [ "/run.sh" ]                    # Laisse s6-overlay piloter le conteneur
