ARG BUILD_FROM
FROM ${BUILD_FROM}

# Paquets système (python, pip, git pour les deps VCS, build deps pour lxml etc.)
RUN apk add --no-cache \
      python3 py3-pip git \
      gcc musl-dev libffi-dev libxml2-dev libxslt-dev

# Venv pour éviter PEP 668 et isoler pip
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"  

# Copie des deps puis install (utilise directement le pip du venv)
COPY requirements.txt /tmp/requirements.txt
RUN /opt/venv/bin/pip install --no-cache-dir \
      --extra-index-url https://wheels.home-assistant.io/musllinux-index/ \
      -r /tmp/requirements.txt

# Copie du code
WORKDIR /app
COPY app/ /app/

# Expose le serveur Flask via Gunicorn
# (Home Assistant Ingress écoute en 8099 par défaut côté add-on)
ENV PYTHONUNBUFFERED=1
CMD ["/opt/venv/bin/gunicorn","-b","0.0.0.0:8099","enocean_manager.app:app"]
