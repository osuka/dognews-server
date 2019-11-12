from .base import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'db.sqlite3',
    }
}

INSTALLED_APPS += (
)

ALLOWED_HOSTS = ['127.0.0.1', 'localhost']
