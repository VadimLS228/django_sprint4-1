from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.generic import (CreateView, DeleteView, DetailView, ListView,
                                  UpdateView)

from .forms import CommentForm, PostForm, ProfileForm
from .models import Category, Post, Comment


User = get_user_model()

NEW_POSTS = 5


class PostListsMixin(ListView):
    """
    Вспомогательный CBV:
    возвращает публикации, сделанные до текущего момента времени
    соответственно запросу по автору, месту и категории.
    """

    model = Post
    paginate_by = 10

    """ Получить список постов в соотв-ии с авторм/местом/категорией. """
    def get_queryset(self):
        queryset = Post.objects.filter(
            is_published=True,
            pub_date__lte=timezone.now(),
            category__is_published=True
        ).order_by('-pub_date').annotate(
            comment_count=Count('comments')
        )
        return queryset


class PostListView(PostListsMixin):
    """ Отображение списка постов на главной странице."""

    template_name = 'blog/index.html'


class CategoryListView(PostListsMixin):
    """ Отображение списка постов конкретной категории."""

    template_name = 'blog/category.html'

    def get_queryset(self, *args, **kwargs):
        self.category = get_object_or_404(
            Category, slug=self.kwargs.get('slug'), is_published=True
        )
        queryset = super().get_queryset(*args, **kwargs).filter(
            category=self.category
        )
        return queryset

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['category'] = self.category
        return context


class ProfileDetailView(PostListsMixin):
    """ Отображение страницы конкретного пользователя со всеми его постами."""

    template_name = 'blog/profile.html'

    def get_queryset(self, *args, **kwargs):
        self.user = get_object_or_404(
            User, username=self.kwargs.get('username')
        )
        if self.user != self.request.user:
            queryset = super().get_queryset(*args, **kwargs).filter(
                author=self.user
            )
        queryset = Post.objects.all().order_by('-pub_date').filter(
            author=self.user
        ).annotate(
            comment_count=Count('comments')
        )
        return queryset

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['profile'] = self.user
        return context


class PostDetailView(DetailView):
    """ Отображение отдельного поста. """

    model = Post
    template_name = 'blog/detail.html'
    pk_url_kwarg = 'post_id'

    def dispatch(self, request, *args, **kwargs):
        post = get_object_or_404(Post, pk=kwargs['post_id'])
        """
        Отфильтровать все посты для авторов публикаций.
        и только опубликованные посты для неавторов.
        """
        if post.author != self.request.user and not post.is_published:
            raise Http404()
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        """ Записать в переменную form пустой объект формы. """
        context['form'] = CommentForm()
        """
        Запросить все комменты для выбранного поста
        Дополнительно подгрузить авторов комментариев.
        """
        context['comments'] = (
            self.object.comments.select_related('author')
        )
        return context


class PostCreateView(LoginRequiredMixin, CreateView):

    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def form_valid(self, form):
        """ Присвоить полю author объект пользователя из запроса. """
        form.instance.author = self.request.user
        """ Продолжить валидацию, описанную в форме. """
        return super().form_valid(form)

    def get_success_url(self):
        username = self.request.user.username
        return reverse('blog:profile', kwargs={'username': username})


class PostRedactMixin(LoginRequiredMixin):

    model = Post
    pk_url_kwarg = 'post_id'

    def dispatch(self, request, *args, **kwargs):
        """ Проверить, является ли пользователь из запроса автором поста. """
        if self.get_object().author != self.request.user:
            """ Если нет-перенаправление на стр поста. """
            return redirect('blog:post_detail', post_id=kwargs['post_id'])
        return super().dispatch(request, args, **kwargs)


class PostUpdateView(PostRedactMixin, UpdateView):

    form_class = PostForm
    template_name = 'blog/create.html'


class PostDeleteView(PostRedactMixin, DeleteView):

    template_name = 'blog/profile.html'

    def get_context_data(self, **kwargs):
        """ получить данные поста по первичному ключу. """
        context = super().get_context_data(**kwargs)
        form = PostForm
        form.instance.post = self.post
        context['form'] = form
        return context

    def get_success_url(self):

        username = self.request.user.username
        return reverse('blog:profile', kwargs={'username': username})


class CommentCreateView(LoginRequiredMixin, CreateView):
    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'

    def form_valid(self, form):
        """
        Переопределить поля формы,присвоив им значения
        автора запроса(комментария) и комментируемого поста.
        """
        form.instance.author = self.request.user
        form.instance.post = get_object_or_404(
            Post, pk=self.kwargs['post_id']
        )
        return super().form_valid(form)


class ProfileUpdateView(LoginRequiredMixin, UpdateView):

    form_class = ProfileForm
    model = User
    template_name = 'blog/user.html'

    def get_object(self):
        """
        получить объект юзера как пользователя из запроса.
        """
        object = self.request.user
        return object

    def get_success_url(self):

        username = self.request.user.username
        return reverse('blog:profile', kwargs={'username': username})


class CommentRedactMixin(LoginRequiredMixin):

    model = Comment
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'

    def dispatch(self, request, *args, **kwargs):
        """ Проверить, является ли польз-ль из запроса автором коммента. """
        if self.get_object().author != self.request.user:
            """ Если нет - перенаправить на страницу деталей поста. """
            return redirect('blog:post_detail', post_id=kwargs['post_id'])
        return super().dispatch(request, args, **kwargs)


class CommentUpdateView(CommentRedactMixin, UpdateView):

    form_class = CommentForm


class CommentDeleteView(CommentRedactMixin, DeleteView):

    def get_success_url(self):
        """ Передать канонический адрес из модели """
        return self.object.get_absolute_url()
    """
    как вариант, потом удалю:
    def get_success_url(self):
        return reverse(
            blog:post_detail', kwargs={'post_id': self.kwargs['post_id']}
        )
    """
