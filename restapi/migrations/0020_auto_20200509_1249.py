# Generated by Django 3.0.6 on 2020-05-09 12:49

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('restapi', '0019_auto_20200508_1742'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='newsitem',
            name='submitter',
        ),
        migrations.AddField(
            model_name='newsitem',
            name='user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.DO_NOTHING, to=settings.AUTH_USER_MODEL),
        ),
    ]