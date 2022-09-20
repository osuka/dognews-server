"""
Settings used when running in "production"
"""

# pylint: disable=wildcard-import, unused-wildcard-import
from .base import *
import dj_database_url

# https://docs.djangoproject.com/en/2.2/ref/settings/#databases

DEBUG = False

DATABASES = {
    # "default": {
    #     "ENGINE": "django.db.backends.mysql",
    #     "NAME": "gatillos_dognews",
    #     "USER": "dognews_dbadmin",
    #     "PASSWORD": "XXXXXXXXXXXXX",
    #     "HOST": MYDBHOST",
    #     "PORT": "3306",
    #     "OPTIONS": {
    #         # Tell MySQLdb to connect with 'utf8mb4' character set
    #         # https://django-mysql.readthedocs.io/en/latest/checks.html#django-mysql-w003-utf8mb4
    #         "charset": "utf8mb4",
    #         # MySQL's Strict Mode fixes many data integrity problems in MySQL, such as data truncation upon
    #         # insertion, by escalating warnings into errors.
    #         # https://docs.djangopSSroject.com/en/2.2/ref/databases/#mysql-sql-mode
    #         "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
    #     },
    # }
    "default": dj_database_url.config(
        default=os.environ["DATABASE_URL"], engine="django_cockroachdb"
    )
}

INSTALLED_APPS += ()

ALLOWED_HOSTS = ["192.168.1.149", "dognewsserver.gatillos.com"]

# to use s3: settings in https://github.com/jschneier/django-storages/blob/master/docs/backends/amazon-S3.rst
DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
# To allow django-admin collectstatic to automatically put your static files in your bucket
STATICFILES_STORAGE = "storages.backends.s3boto3.S3StaticStorage"
# if we use https://docs.djangoproject.com/en/3.1/ref/contrib/staticfiles/#manifeststaticfilesstorage
# STATICFILES_STORAGE = "storages.backends.s3boto3.S3ManifestStaticStorage"
# credentials are provided via environment AWS instance profile
AWS_S3_SESSION_PROFILE = os.environ.get("AWS_PROFILE", "onlydognews-local-server")
AWS_LOCATION = "prod"  # prefix
AWS_STORAGE_BUCKET_NAME = "onlydognews.com"
