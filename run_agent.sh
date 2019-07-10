#!/bin/bash

if [ -f .env ]; then
  . .env
fi

env
/bin/bash install.sh

env/bin/celery -A app.celery worker --loglevel=info
