from django.contrib.auth import get_user_model
from django.db.models import Count
from django.shortcuts import redirect
from django.utils import timezone
from django.views.generic import ListView

from .models import Comment, Post

User = get_user_model()


class PostListsMixin(ListView):
    """
    Вспомогательный CBV:
    возвращает публикации, сделанные до текущего момента времени
    соответственно запросу по автору, месту и категории.
    """

    model = Post
    paginate_by = 10

    def get_queryset(self, *args, **kwargs):
        """Получить список постов в соотв-ии с авторм/местом/категорией."""
        return (
            Post.objects.select_related("author", "category", "location")
            .filter(
                is_published=True,
                pub_date__lte=timezone.now(),
                category__is_published=True,
            )
            .order_by("-pub_date")
            .annotate(comment_count=Count("comments"))
        )


class PostRedactMixin():
    model = Post
    template_name = "blog/create.html"
    pk_url_kwarg = "post_id"

    def dispatch(self, request, *args, **kwargs):
        """Проверить, является ли пользователь из запроса автором поста.
        Если нет-перенаправление на стр поста.
        """
        if self.get_object().author != self.request.user:
            return redirect("blog:post_detail", post_id=kwargs["post_id"])
        return super().dispatch(request, args, **kwargs)


class CommentRedactMixin():
    model = Comment
    template_name = "blog/comment.html"
    pk_url_kwarg = "comment_id"

    def dispatch(self, request, *args, **kwargs):
        """Проверить, является ли польз-ль из запроса автором коммента.
        Если нет - перенаправить на страницу деталей поста.
        """
        if self.get_object().author != self.request.user:
            return redirect("blog:post_detail", post_id=kwargs["post_id"])
        return super().dispatch(request, args, **kwargs)
