# Generated by Django 2.2.7 on 2019-11-12 18:34

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('restapi', '0009_auto_20191112_1824'),
    ]

    operations = [
        migrations.AlterField(
            model_name='rating',
            name='newsItem',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='ratings', to='restapi.NewsItem'),
        ),
    ]