from django.contrib import admin

from .models import Category, Comment, Location, Post


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Модель категории отображена в админ-панели.
    Можно удалить/опубликовать или сменить слаг.
    """

    list_display = (
        "title", "description", "slug", "is_published", "created_at"
    )
    list_editable = ("is_published", "slug")
    search_fields = (
        "title",
        "slug",
    )
    list_display_links = ("title",)


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    """Локация отображена в админ-панели. Можно удалить/опубликовать."""

    list_display = ("name", "is_published", "created_at")
    list_editable = ("is_published",)
    search_fields = ("name",)
    list_display_links = ("name",)


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    """Публикации отображены в админ-панели.
    Можно удалить/опубликовать и переместить в другую категорию.
    """

    list_display = (
        "title", "author", "category", "text", "is_published", "created_at"
    )
    list_editable = ("is_published", "category")
    search_fields = (
        "title",
        "author",
    )
    list_filter = ("category",)
    list_display_links = ("title",)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    """Комментарии отображены в админ-панели.
    Можно снять с публикации оскорбительный коммент/спам.
    """

    list_display = ("post", "text", "is_published", "created_at")
    list_editable = ("is_published",)
    search_fields = (
        "post",
        "text",
    )
    list_display_links = ("post",)
