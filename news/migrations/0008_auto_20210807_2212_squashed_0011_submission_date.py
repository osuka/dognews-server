# Generated by Django 3.2.5 on 2021-08-07 23:06

from django.db import migrations, models


class Migration(migrations.Migration):

    replaces = [
        ("news", "0008_auto_20210807_2212"),
        ("news", "0009_auto_20210807_2218"),
        ("news", "0010_alter_submission_fetched_page"),
        ("news", "0011_submission_date"),
    ]

    dependencies = [
        ("news", "0007_alter_submission_owner"),
    ]

    operations = [
        migrations.AlterField(
            model_name="submission",
            name="fetched_date",
            field=models.DateTimeField(editable=False, null=True),
        ),
        migrations.AlterField(
            model_name="submission",
            name="fetched_page",
            field=models.TextField(
                blank=True, default="", editable=False, max_length=61440
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="submission",
            name="date",
            field=models.DateTimeField(null=True),
        ),
    ]
