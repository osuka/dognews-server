#!/bin/bash

cd /app

if [[ "${ENVIRONMENT}" == "" ]]; then
  echo "ABORT: Please supply ENVIRONMENT value"
  exit 1
fi

source .venv/bin/activate
export DJANGO_SETTINGS_MODULE=dognews.settings.${ENVIRONMENT}

python3 manage.py migrate
python3 manage.py collectstatic --noinput

