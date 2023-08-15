# Generated by Django 3.2.16 on 2023-07-09 17:50

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("blog", "0008_post_comments"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="comment",
            options={
                "ordering": ("created_at",),
                "verbose_name": "комментарий",
                "verbose_name_plural": "Комментарии",
            },
        ),
        migrations.RemoveField(
            model_name="post",
            name="comments",
        ),
        migrations.AddField(
            model_name="comment",
            name="post",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="posts",
                to="blog.post",
            ),
        ),
        migrations.AddField(
            model_name="post",
            name="image",
            field=models.ImageField(
                blank=True, upload_to="birthdays_images", verbose_name="Фото"
            ),
        ),
        migrations.AlterField(
            model_name="comment",
            name="author",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to=settings.AUTH_USER_MODEL,
                verbose_name="{author} прокомментировал: ",
            ),
        ),
        migrations.AlterField(
            model_name="comment",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True, verbose_name="Добавлено"),
        ),
    ]
