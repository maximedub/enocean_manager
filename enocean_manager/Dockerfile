# Dockerfile (in your add-on folder)
ARG BUILD_FROM
FROM ${BUILD_FROM}

# System deps
RUN apk add --no-cache \
    python3 py3-pip \
    git \
    gcc musl-dev libffi-dev \
    libxml2-dev libxslt-dev

# Create & use venv (avoids PEP 668)
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:${PATH}"

# Python deps (VCS install needs git)
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir \
      --extra-index-url https://wheels.home-assistant.io/musllinux-index/ \
      -r /tmp/requirements.txt

# App code
WORKDIR /opt/enocean_manager
COPY . /opt/enocean_manager

# s6-overlay calls /run.sh
CMD [ "/run.sh" ]
