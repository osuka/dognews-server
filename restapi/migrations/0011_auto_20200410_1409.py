# Generated by Django 3.0.2 on 2020-04-10 14:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('restapi', '0010_auto_20191112_1834'),
    ]

    operations = [
        migrations.AlterField(
            model_name='newsitem',
            name='cached_page',
            field=models.CharField(blank=True, default=None, max_length=120, null=True),
        ),
        migrations.AlterField(
            model_name='newsitem',
            name='image',
            field=models.CharField(blank=True, default=None, max_length=250, null=True),
        ),
        migrations.AlterField(
            model_name='newsitem',
            name='source',
            field=models.CharField(max_length=250),
        ),
        migrations.AlterField(
            model_name='newsitem',
            name='thumbnail',
            field=models.CharField(blank=True, default=None, max_length=120, null=True),
        ),
    ]
