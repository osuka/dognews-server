# Generated by Django 2.2.7 on 2019-11-12 11:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('restapi', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='newsitem',
            name='body',
            field=models.CharField(blank=True, default=None, max_length=512, null=True),
        ),
        migrations.AlterField(
            model_name='newsitem',
            name='cached_page',
            field=models.CharField(blank=True, default=None, max_length=80, null=True),
        ),
        migrations.AlterField(
            model_name='newsitem',
            name='image',
            field=models.CharField(blank=True, default=None, max_length=80, null=True),
        ),
        migrations.AlterField(
            model_name='newsitem',
            name='sentiment',
            field=models.CharField(blank=True, default=None, max_length=20, null=True),
        ),
        migrations.AlterField(
            model_name='newsitem',
            name='summary',
            field=models.CharField(blank=True, default=None, max_length=4096, null=True),
        ),
        migrations.AlterField(
            model_name='newsitem',
            name='thumbnail',
            field=models.CharField(blank=True, default=None, max_length=80, null=True),
        ),
        migrations.AlterField(
            model_name='newsitem',
            name='type',
            field=models.CharField(blank=True, default=None, max_length=50, null=True),
        ),
    ]
