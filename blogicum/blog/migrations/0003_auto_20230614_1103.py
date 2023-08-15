# Generated by Django 3.2.16 on 2023-06-14 11:03

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("blog", "0002_auto_20230614_1055"),
    ]

    operations = [
        migrations.AlterField(
            model_name="location",
            name="is_published",
            field=models.BooleanField(
                default=True,
                help_text="Снимите галочку, чтобы скрыть публикацию.",
                verbose_name="Опубликовано",
            ),
        ),
        migrations.AlterField(
            model_name="post",
            name="is_published",
            field=models.BooleanField(
                default=True,
                help_text="Снимите галочку, чтобы скрыть публикацию.",
                verbose_name="Опубликовано",
            ),
        ),
    ]
