FROM python:3.11-slim

# Installer les dépendances système + git
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

# Outils Python de compilation
RUN pip install --upgrade pip setuptools wheel

# Dépendances Python
RUN pip install --no-cache-dir \
    flask \
    beautifulsoup4 \
    lxml \
    git+https://github.com/kipe/enocean.git

COPY run.sh /run.sh
COPY app /app

WORKDIR /app

CMD ["/run.sh"]
