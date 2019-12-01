# Generated by Django 2.2.7 on 2019-11-12 18:09

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('restapi', '0006_auto_20191112_1758'),
    ]

    operations = [
        migrations.AddField(
            model_name='rating',
            name='newsItem',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, to='restapi.NewsItem'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='newsitem',
            name='ratings',
            field=models.ManyToManyField(blank=True, related_name='ratings', to='restapi.Rating'),
        ),
    ]