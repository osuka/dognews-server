"""
Settings auto loaded when running tests
"""

# pylint: disable=wildcard-import, unused-wildcard-import
from .base import *

# Important!
#
# https://docs.djangoproject.com/en/2.2/topics/testing/overview/#the-test-database

REST_FRAMEWORK["DEFAULT_THROTTLE_CLASSES"] = []  # disable throttling in tests

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "testdb.sqlite3",
    }
}

INSTALLED_APPS += ()

ALLOWED_HOSTS = ["127.0.0.1", "localhost"]
