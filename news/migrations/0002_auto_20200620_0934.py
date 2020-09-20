# Generated by Django 3.0.6 on 2020-06-20 09:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('news', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='moderatedsubmission',
            name='description',
            field=models.CharField(default=None, max_length=250, null=True),
        ),
        migrations.AlterField(
            model_name='moderatedsubmission',
            name='target_url',
            field=models.URLField(default=None, null=True, unique=True),
        ),
        migrations.AlterField(
            model_name='moderatedsubmission',
            name='title',
            field=models.CharField(default=None, max_length=120, null=True),
        ),
    ]