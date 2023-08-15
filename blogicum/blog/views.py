from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import CreateView, DeleteView, DetailView, UpdateView

from .forms import CommentForm, PostForm, ProfileForm
from .mixins import CommentRedactMixin, PostListsMixin
from .models import Category, Comment, Post

User = get_user_model()

NEW_POSTS = 5


class PostListView(PostListsMixin):
    """Отображение списка постов на главной странице."""

    template_name = "blog/index.html"


class CategoryListView(PostListsMixin):
    """Отображение списка постов конкретной категории."""

    template_name = "blog/category.html"

    def get_queryset(self, *args, **kwargs):
        self.category = get_object_or_404(
            Category, slug=self.kwargs.get("slug"), is_published=True
        )
        queryset = super().get_queryset(*args, **kwargs).filter(
            category=self.category
        )
        return queryset

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["category"] = self.category
        return context


class ProfileDetailView(PostListsMixin):
    """Отображение страницы конкретного пользователя со всеми его постами."""

    template_name = "blog/profile.html"

    def get_queryset(self, *args, **kwargs):
        self.user = get_object_or_404(
            User, username=self.kwargs.get("username")
        )
        if self.user != self.request.user:
            queryset = super().get_queryset(*args, **kwargs).filter(
                author=self.user
            )
        queryset = (
            Post.objects.select_related("author", "category", "location")
            .all()
            .order_by("-pub_date")
            .filter(author=self.user)
            .annotate(comment_count=Count("comments"))
        )
        return queryset

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["profile"] = self.user
        return context


class PostDetailView(DetailView):
    """Отображение отдельного поста."""

    model = Post
    template_name = "blog/detail.html"
    pk_url_kwarg = "post_id"

    def get_object(self):
        """
        Определить автор или не автор делает запрос.
        Показать любой пост автору и только если опубликован - не автору.
        """
        pk = self.kwargs.get("post_id")
        object = Post.objects.filter(pk=pk)
        post = get_object_or_404(Post, id=self.kwargs["post_id"])
        if post.author != self.request.user and not post.is_published:
            raise Http404()
        return object.get()

    def get_context_data(self, **kwargs):
        """
        Запросить все комменты для выбранного поста
        Дополнительно подгрузить авторов комментариев.
        """

        context = super().get_context_data(**kwargs)
        context["form"] = CommentForm()
        context["comments"] = self.object.comments.select_related("author")
        return context


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = "blog/create.html"

    def form_valid(self, form):
        """Присвоить полю author объект пользователя из запроса.
        Продолжить валидацию, описанную в форме.
        """

        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        username = self.request.user.username
        return reverse("blog:profile", kwargs={"username": username})


class PostRedactMixin(LoginRequiredMixin):
    model = Post
    pk_url_kwarg = "post_id"

    def dispatch(self, request, *args, **kwargs):
        """Проверить, является ли пользователь из запроса автором поста.
        Если нет-перенаправление на стр поста.
        """

        if self.get_object().author != self.request.user:
            return redirect("blog:post_detail", post_id=kwargs["post_id"])
        return super().dispatch(request, args, **kwargs)


class PostUpdateView(PostRedactMixin, UpdateView):
    form_class = PostForm
    template_name = "blog/create.html"


class PostDeleteView(PostRedactMixin, DeleteView):
    template_name = "blog/create.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        PostForm().instance.post = self.post
        return context

    def get_success_url(self):
        username = self.request.user.username
        return reverse("blog:profile", kwargs={"username": username})


class CommentCreateView(LoginRequiredMixin, CreateView):
    model = Comment
    form_class = CommentForm
    template_name = "blog/comment.html"

    def form_valid(self, form):
        """Переопределить поля формы,присвоив им значения
        автора запроса(комментария) и комментируемого поста.
        """

        form.instance.author = self.request.user
        form.instance.post = get_object_or_404(Post, pk=self.kwargs["post_id"])
        return super().form_valid(form)


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    form_class = ProfileForm
    model = User
    template_name = "blog/user.html"

    def get_object(self):
        """Получить объект юзера как пользователя из запроса."""

        return self.request.user

    def get_success_url(self):
        username = self.request.user.username
        return reverse("blog:profile", kwargs={"username": username})


class CommentUpdateView(LoginRequiredMixin, CommentRedactMixin, UpdateView):

    form_class = CommentForm


class CommentDeleteView(LoginRequiredMixin, CommentRedactMixin, DeleteView):

    def get_success_url(self):
        """Передать канонический адрес из модели"""
        return self.object.get_absolute_url()
