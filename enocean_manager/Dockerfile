# Base Home Assistant (PEP 668) + venv pour pip
ARG BUILD_FROM=ghcr.io/home-assistant/aarch64-base:latest
FROM ${BUILD_FROM}

RUN apk add --no-cache python3 py3-pip gcc musl-dev libffi-dev

# Créer un venv pour installer les libs Python
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:${PATH}"

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY . /opt/enocean_manager

RUN mkdir -p /data/profile_json && \
    if [ -d "/opt/enocean_manager/app/profile_json" ]; then \
      cp -r /opt/enocean_manager/app/profile_json/* /data/profile_json/ || true; \
    fi

COPY run.sh /run.sh
RUN chmod +x /run.sh

CMD [ "/run.sh" ]
