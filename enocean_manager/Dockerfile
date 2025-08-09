ARG BUILD_FROM=ghcr.io/home-assistant/amd64-base:3.19
FROM ${BUILD_FROM}

RUN apk add --no-cache python3 py3-pip

WORKDIR /app
COPY requirements.txt /app/
RUN pip3 install --no-cache-dir -r /app/requirements.txt

COPY app.py /app/
COPY enocean_esp3.py /app/
COPY eep_loader.py /app/
COPY yaml_writer.py /app/
COPY run.sh /app/
RUN chmod +x /app/run.sh

# Dossier EEP par défaut (vous pourrez aussi monter le vôtre)
RUN mkdir -p /app/eep_json

CMD ["/app/run.sh"]
