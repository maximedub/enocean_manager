# Dockerfile
ARG BUILD_FROM
FROM $BUILD_FROM

# System deps (python, build tools, and git for VCS requirements)
RUN apk add --no-cache \
    python3 py3-pip \
    gcc musl-dev libffi-dev libxml2-dev libxslt-dev \
    git

# Create and use a venv
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Copy requirements first (better cache)
COPY requirements.txt /tmp/requirements.txt
RUN /opt/venv/bin/pip install --no-cache-dir \
    --extra-index-url https://wheels.home-assistant.io/musllinux-index/ \
    -r /tmp/requirements.txt

# Copy the app
WORKDIR /app
COPY enocean_manager /app/enocean_manager
COPY templates /app/templates
COPY run.sh /run.sh
RUN chmod +x /run.sh

# The HA supervisor provides S6. With S6 v3 you normally set init: false in config.yaml.
# We’ll use our run.sh as the command.
CMD [ "/run.sh" ]
