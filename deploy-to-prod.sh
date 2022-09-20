#!/bin/bash

source ./config.local.sh

export DATABASE_URL="${PROD_DATABASE_URL}"
export AWS_PROFILE="${PROD_AWS_PROFILE}"
export DJANGO_SETTINGS_MODULE=dognews.settings.prod

echo "Make sure all static data is deployed"
./manage.py collectstatic

echo "Make sure the database is populated"
./manage.py migrate
