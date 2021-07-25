# Generated by Django 3.2.5 on 2021-07-25 09:39

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('news', '0006_auto_20201007_1216'),
    ]

    operations = [
        migrations.AlterField(
            model_name='submission',
            name='owner',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='submissions', to=settings.AUTH_USER_MODEL),
        ),
    ]
