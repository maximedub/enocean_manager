#!/bin/sh
cd /app
exec gunicorn -b 0.0.0.0:8099 main:app
