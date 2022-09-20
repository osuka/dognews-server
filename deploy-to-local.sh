#!/bin/bash

source ./config.local.sh

export DATABASE_URL="${LOCAL_DATABASE_URL}"
export AWS_PROFILE="${LOCAL_AWS_PROFILE}"
export DJANGO_SETTINGS_MODULE=dognews.settings.local

echo "Make sure all static data is deployed"
./manage.py collectstatic

echo "Make sure the database is populated"
./manage.py migrate
