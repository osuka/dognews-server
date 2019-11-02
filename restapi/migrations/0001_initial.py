# Generated by Django 2.2.6 on 2019-11-02 23:32

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='NewsItem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('target_url', models.CharField(max_length=250, unique=True)),
                ('date', models.DateTimeField(default=django.utils.timezone.now)),
                ('title', models.CharField(max_length=250)),
                ('source', models.CharField(max_length=80)),
                ('submitter', models.CharField(max_length=25)),
                ('fetch_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('image', models.CharField(blank=True, default=None, max_length=80)),
                ('type', models.CharField(blank=True, default=None, max_length=50)),
                ('body', models.CharField(blank=True, default=None, max_length=512)),
                ('cached_page', models.CharField(blank=True, default=None, max_length=80)),
                ('thumbnail', models.CharField(blank=True, default=None, max_length=80)),
                ('summary', models.CharField(blank=True, default=None, max_length=4096)),
                ('sentiment', models.CharField(blank=True, default=None, max_length=20)),
            ],
        ),
        migrations.CreateModel(
            name='NewsItemRating',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rating', models.IntegerField(default=0)),
                ('date', models.DateTimeField(default=django.utils.timezone.now)),
                ('newsItem', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='restapi.NewsItem')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
