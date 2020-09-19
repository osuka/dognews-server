"""
globally needed models
"""
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """We reuse the standard user model in Django as recommended
    see AUTH_USER_MODEL in settings.py that *must* point to this
    """
