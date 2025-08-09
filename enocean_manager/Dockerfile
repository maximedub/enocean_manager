ARG BUILD_FROM
FROM ${BUILD_FROM}

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

# Python + venv (évite PEP 668)
RUN apk add --no-cache python3 py3-pip \
 && python3 -m venv /opt/venv

WORKDIR /app

# Dépendances Python dans le venv
COPY requirements.txt /app/
RUN /opt/venv/bin/pip install --no-cache-dir -r /app/requirements.txt

# Code
COPY app.py /app/
COPY enocean_esp3.py /app/
COPY eep_loader.py /app/
COPY yaml_writer.py /app/
COPY run.sh /app/
RUN chmod +x /app/run.sh

# ⚠️ Copier depuis le chemin réel du repo
COPY app/profile_json /app/profile_json

CMD ["/app/run.sh"]
