#!/bin/sh

if [ -f .env ]; then
  /bin/sh .env
fi

/bin/sh install.sh

env/bin/uwsgi --yaml /etc/uwsgi.yaml --http "${LISTEN_ON:-0.0.0.0}:${LISTEN_PORT:-5000}" --py-autoreload 1
