FROM python:3.11-alpine

RUN apk add --no-cache build-base libffi-dev py3-pip curl \
    && pip install flask python-enocean beautifulsoup4 lxml

COPY run.sh /run.sh
COPY app /app

RUN chmod +x /run.sh

CMD ["/run.sh"]
