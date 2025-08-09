ARG BUILD_FROM
FROM ${BUILD_FROM}

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

RUN apk add --no-cache python3 py3-pip \
 && python3 -m venv /opt/venv

WORKDIR /app

COPY requirements.txt /app/
RUN /opt/venv/bin/pip install --no-cache-dir -r /app/requirements.txt

COPY app.py /app/
COPY enocean_esp3.py /app/
COPY eep_loader.py /app/
COPY yaml_writer.py /app/
COPY run.sh /app/
RUN chmod +x /app/run.sh

# ⇩ Gardez UNE SEULE des deux lignes selon votre variante
# VARIANTE A (embarqué) :
# COPY eep_json /app/eep_json

# VARIANTE B (persistant) :
# RUN mkdir -p /app/eep_json

CMD ["/app/run.sh"]
