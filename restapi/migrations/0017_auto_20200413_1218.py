# Generated by Django 3.0.5 on 2020-04-13 12:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("restapi", "0016_auto_20200413_1217"),
    ]

    operations = [
        migrations.AlterField(
            model_name="newsitem",
            name="publication_state",
            field=models.CharField(
                blank=True,
                choices=[
                    ("P", "Published"),
                    ("A", "Approved"),
                    ("D", "Discarded"),
                    ("", "-"),
                ],
                default="",
                max_length=1,
                verbose_name="PubStatus",
            ),
        ),
    ]
