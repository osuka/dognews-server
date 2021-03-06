""" Helper functions for repeated code that appears in tests

django caveat: we can't use the data that is populated during the migrations because we are in a transaction
and that data hasn't been commited to db when they run, so eg Permissions aren't found

we recreate the two groups: basic_users and admin  TODO: better way?
these give access to the model, there are other per-object permissions

"""

# pylint: disable=missing-class-docstring, missing-function-docstring

import random
from typing import List
from django.db.models import Model
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission


def _user(prefix: str, suffix: str, perms: List[Permission], admin: bool = False):
    groupname = f"{prefix}-{suffix}"
    username = f"{prefix}-{suffix}"
    group, _ = Group.objects.get_or_create(name=groupname)
    group.save()
    group.permissions.add(*Permission.objects.filter(codename__in=perms))
    user, _ = get_user_model().objects.get_or_create(
        username=username,
        email="nothing@example.com",
        password=f"x{random.random()}X",
    )
    if admin and not user.is_staff:
        user.is_staff = True
        user.save()
    if not group in user.groups.all():
        user.groups.add(group)
    return user


def ro_for(models: List[Model], suffix: str = "", admin: bool = False):
    perms = []
    for model in models:
        entity = model._meta.model_name
        perms += [f"view_{entity}"]
    return _user("ro", suffix + ("user" if not admin else "admin"), perms, admin)


def rw_for(models: List[Model], suffix: str = "", admin: bool = False):
    perms = []
    for model in models:
        entity = model._meta.model_name
        perms += [
            f"view_{entity}",
            f"add_{entity}",
            f"change_{entity}",
            f"delete_{entity}",
        ]

    return _user("rw", suffix + ("user" if not admin else "admin"), perms, admin)
