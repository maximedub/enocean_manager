FROM python:3.11-slim

# Installer les dépendances système nécessaires
RUN apt-get update && \
    apt-get install -y \
        build-essential \
        libffi-dev \
        libxml2-dev \
        libxslt1-dev \
        zlib1g-dev \
        curl \
        && rm -rf /var/lib/apt/lists/*

# Installer les packages Python
RUN pip install --no-cache-dir \
    flask \
    python-enocean \
    beautifulsoup4 \
    lxml

# Copier les fichiers
COPY run.sh /run.sh
COPY app /app

WORKDIR /app

CMD ["/run.sh"]
