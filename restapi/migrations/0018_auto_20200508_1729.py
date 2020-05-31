# Generated by Django 3.0.6 on 2020-05-08 17:29

from django.db import migrations


def create_admin_group(apps, schema_editor):
    # very important to not import directly the model
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")
    admin_group, _ = Group.objects.get_or_create(name=f"admin")
    admin_group.permissions.add(
        *Permission.objects.filter(
            codename__in=[
                "view_newsitem",
                "add_newsitem",
                "change_newsitem",
                "delete_newsitem",
                "view_rating",
                "add_rating",
                "change_rating",
                "delete_rating",
            ]
        )
    )
    admin_group.save()

    # the 'admin' group has special meaning in terms of permissions
    # and is used to give permissions to modify _other_ users data


class Migration(migrations.Migration):

    dependencies = [
        ("restapi", "0017_auto_20200413_1218"),
    ]

    operations = [
        migrations.RunPython(create_admin_group),
    ]