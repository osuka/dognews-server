# Generated by Django 3.2.5 on 2021-08-11 00:02

from django.db import migrations, models
import news.models


class Migration(migrations.Migration):

    dependencies = [
        ('news', '0009_auto_20210808_2153_squashed_0022_alter_vote_submission'),
    ]

    operations = [
        migrations.AlterField(
            model_name='fetch',
            name='thumbnail_image',
            field=models.ImageField(blank=True, null=True, upload_to=news.models.user_directory_path),
        ),
    ]
