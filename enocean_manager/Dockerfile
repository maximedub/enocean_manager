# Utilise une image Python compatible multi-architecture
FROM --platform=$BUILDPLATFORM python:3.11-slim

# Installer les dépendances système
RUN apt-get update && \
    apt-get install -y \
        build-essential \
        libffi-dev \
        libxml2-dev \
        libxslt1-dev \
        zlib1g-dev \
        curl \
        git \
    && rm -rf /var/lib/apt/lists/*

# Installer les dépendances Python
RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir \
        flask \
        gunicorn \
        requests \
        beautifulsoup4 \
        lxml \
        git+https://github.com/kipe/enocean.git

# Copie des fichiers de l'application
COPY run.sh /run.sh
COPY app /app

# Définir le dossier de travail
WORKDIR /app

# Expose le port utilisé par Gunicorn / Flask
EXPOSE 5000

# Point d’entrée
CMD ["/bin/bash", "/run.sh"]
