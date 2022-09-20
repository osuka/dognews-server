# create_passenger_configuration
# See https://help.dreamhost.com/hc/en-us/articles/215769548-Passenger-and-Python-WSGI
# Dreamhost's passenger configuration requires a custom entry point that
# switches python interpreters
import sys
import os
from django.core.wsgi import get_wsgi_application
INTERP = "./.venv/bin/python3"
# INTERP is present twice so that the new Python interpreter knows
# the actual executable path
if sys.executable != INTERP:
    os.execl(INTERP, INTERP, *sys.argv)
# the rest of this file is the standard django wsgi.py
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dognews.settings.${ENVIRONMENT}')
application = get_wsgi_application()
