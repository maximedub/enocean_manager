# IMPORTANT : laissez le Supervisor injecter l'image de base
ARG BUILD_FROM
FROM ${BUILD_FROM}

# Variables d'env utiles
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

# Dépendances système minimales + création du venv
RUN apk add --no-cache python3 py3-pip \
 && python3 -m venv /opt/venv

WORKDIR /app

# Dépendances Python dans le venv (contourne PEP 668)
COPY requirements.txt /app/
RUN /opt/venv/bin/pip install --no-cache-dir -r /app/requirements.txt

# Code de l’add-on
COPY app.py /app/
COPY enocean_esp3.py /app/
COPY eep_loader.py /app/
COPY yaml_writer.py /app/
COPY run.sh /app/
RUN chmod +x /app/run.sh

# Profils EEP embarqués (si vous les packez dans l'image)
# Sinon, supprimez cette ligne et pointez eep_dir vers /config/...
COPY profile_json /app/profile_json

CMD ["/app/run.sh"]
