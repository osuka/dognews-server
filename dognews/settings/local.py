"""
Settings for running the server in a dev machine locally
"""
# pylint: disable=wildcard-import, unused-wildcard-import

from .base import *
import dj_database_url

DATABASES = {
    # "default": {
    #     "ENGINE": "django.db.backends.sqlite3",
    #     "NAME": "db.sqlite3",
    # }
    "default": dj_database_url.config(
        default=os.environ["DATABASE_URL"],
        engine="django_cockroachdb",
        ssl_require=True,
    )
}

INSTALLED_APPS += ()

ALLOWED_HOSTS = ["127.0.0.1", "localhost", "10.0.2.2", "172.17.0.1"]
# note: 10.0.2.2 is what android emulator connects from
# note: 172.17.0.1 is what is exposed when running from inside a container

DEBUG = True

# https://github.com/jschneier/django-storages

# to use s3: settings in https://github.com/jschneier/django-storages/blob/master/docs/backends/amazon-S3.rst
DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
# To allow django-admin collectstatic to automatically put your static files in your bucket
STATICFILES_STORAGE = "storages.backends.s3boto3.S3StaticStorage"
# if we use https://docs.djangoproject.com/en/3.1/ref/contrib/staticfiles/#manifeststaticfilesstorage
# STATICFILES_STORAGE = "storages.backends.s3boto3.S3ManifestStaticStorage"
# credentials are provided per environment (AWS instance profile, aws env var etc)
AWS_S3_SESSION_PROFILE = os.environ.get("AWS_PROFILE", "onlydognews-local-server")
AWS_LOCATION = "local"  # prefix
AWS_STORAGE_BUCKET_NAME = "onlydognews.com"

# to use sftp: settings in https://github.com/jschneier/django-storages/blob/master/docs/backends/sftp.rst
# DEFAULT_FILE_STORAGE = "storages.backends.sftpstorage.SFTPStorage"
# SFTP_STORAGE_HOST = "minion"
# SFTP_STORAGE_ROOT = "/tmp/dognewsphotos"
# SFTP_STORAGE_PARAMS = {"username": "osuka"}
# SFTP_STORAGE_INTERACTIVE = False
# SFTP_STORAGE_FILE_MODE = (
#     0o664  # or stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH
# )
# # SFTP_STORAGE_UID =
# # SFTP_STORAGE_GID =
# # SFTP_KNOWN_HOST_FILE =
