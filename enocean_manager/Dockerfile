FROM python:3.11-slim

RUN apt-get update && \
    apt-get install -y build-essential libffi-dev curl && \
    pip install --no-cache-dir flask python-enocean beautifulsoup4 lxml

COPY run.sh /run.sh
COPY app /app

WORKDIR /app

CMD ["/run.sh"]
