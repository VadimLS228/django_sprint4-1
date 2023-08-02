# from typing import Any, Dict
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.db.models import Q
# from django.forms.models import BaseModelForm
from django.http import HttpResponse
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


@login_required
def simple_view(request):
    return HttpResponse('Страница для залогиненных пользователей!')


class HelpList(ListView):
    """
    Вспомогательный CBV:
    возвращает публикации, сделанные до текущего момента времени
    соответственно запросу по автору, месту и категории.
    """

    model = Post
    paginate_by = 10

    # Получить список постов в соотв-ии с авторм/местом/категорией.
    def get_queryset(self, *args, **kwargs):
        queryset = super().get_queryset(*args, **kwargs)
        # Отфильтровать все посты для авторов публикаций
        queryset = Post.objects.select_related(
            'author', 'location', 'category').filter(
            Q(author__username=self.request.user.username) & Q(
                category__is_published=True) | ~Q(
                #  и только опубликованные посты для неавторов.
                author__username=self.request.user.username) & Q(
                is_published=True) & Q(
                category__is_published=True) & Q(
                pub_date__lte=timezone.now())
            )
        return queryset


class PostListView(HelpList):
    '''Отображение списка постов на главной странице.'''

    template_name = 'blog/index.html'

    def get_queryset(self, *args, **kwargs):
        queryset = super().get_queryset(*args, **kwargs)
        queryset = Post.objects.filter(
            is_published=True,
            pub_date__lte=timezone.now(),
            category__is_published=True
        ).order_by('-pub_date').annotate(
            comment_count=Count('comments')
        )
        return queryset


class CategoryListView(HelpList):
    '''Отображение списка постов конкретной категории.'''

    template_name = 'blog/category.html'

    def get_queryset(self, *args, **kwargs):
        queryset = super().get_queryset(*args, **kwargs)
        category = get_object_or_404(
            Category, slug=self.kwargs.get('slug'), is_published=True
        )
        queryset = Post.objects.filter(
            category=category, is_published=True, pub_date__lte=timezone.now()
        ).order_by('-pub_date').annotate(
            comment_count=Count('comments')
        )
        return queryset

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['category'] = get_object_or_404(
            Category, slug=self.kwargs.get('slug')
        )
        return context


class ProfileDetailView(HelpList):
    '''Отображение страницы конкретного пользователя со всеми его постами.'''

    template_name = 'blog/profile.html'

    def get_queryset(self, *args, **kwargs):
        queryset = super().get_queryset(*args, **kwargs)
        user = get_object_or_404(User, username=self.kwargs.get('username'))
        queryset = Post.objects.filter(
            author=user).order_by('-pub_date').annotate(
            comment_count=Count('comments')
        )
        return queryset

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['profile'] = get_object_or_404(
            User, username=self.kwargs.get('username')
        )
        return context


class PostDetailView(DetailView):
    '''Отображение отдельного поста.'''

    model = Post
    template_name = 'blog/detail.html'
    pk_url_kwarg = 'post_id'

    def get_object(self):
        # obj = get_object_or_404(Post, pk=self.kwargs['post_id'])
        post = super().get_object()
        if (
            post.author != self.request.user) and (
            not post.is_published or (post.pub_date > timezone.now())
            or not post.category.is_published
        ):
            raise Http404
        return post

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Записать в переменную form пустой объект формы.
        context['form'] = CommentForm()
        # Запросить все комменты для выбранного поста
        # Дополнительно подгрузить авторов комментариев
        context['comments'] = (
            self.object.comments.select_related('author')
        )
        return context


class PostCreateView(LoginRequiredMixin, CreateView):

    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def form_valid(self, form):
        # Присвоить полю author объект пользователя из запроса.
        form.instance.author = self.request.user
        # Продолжить валидацию, описанную в форме.
        return super().form_valid(form)

    def get_success_url(self):
        username = self.request.user.username
        return reverse('blog:profile', kwargs={'username': username})


class PostUpdateView(LoginRequiredMixin, UpdateView):

    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'

    def dispatch(self, request, *args, **kwargs):
        # Проверить, является ли пользователь из запроса автором поста.
        if self.get_object().author != self.request.user:
            # Если нет-перенаправление на стр поста.
            return redirect('blog:post_detail', post_id=kwargs['post_id'])
        return super().dispatch(request, args, **kwargs)

    def get_context_data(self, **kwargs):
        # получить данные поста по первичному ключу.
        context = super().get_context_data(**kwargs)
        context['post'] = get_object_or_404(Post, pk=self.kwargs['post_id'])
        return context

    def form_valid(self, form):
        # Приcвоить полю author объект пользователя из запроса.
        form.instance.author = self.request.user
        # Продолжить валидацию, описанную в форме
        return super().form_valid(form)

    def get_success_url(self):
        post_id = self.get_object().pk
        return reverse(
            'blog:post_detail', kwargs={'post_id': post_id}
        )


class ProfileUpdateView(LoginRequiredMixin, UpdateView):

    form_class = ProfileForm
    model = User
    template_name = 'blog/user.html'
    context_object_name = 'user'
    queryset = User.objects.all()

    def get_context_data(self, **kwargs):
        # получить данные профиля по первичному ключу.
        instance = get_object_or_404(User, pk=self.kwargs.get('pk'))
        form = ProfileForm(instance=instance)
        context = super().get_context_data(**kwargs)
        context['form'] = form
        return context

    def get_success_url(self):
        username = self.request.user.username
        return reverse('blog:profile', kwargs={'username': username})


class PostDeleteView(LoginRequiredMixin, DeleteView):

    model = Post
    template_name = 'blog/profile.html'
    pk_url_kwarg = 'post_id'

    def dispatch(self, request, *args, **kwargs):
        # Проверить, является ли пользователь из запроса автором поста.
        if self.get_object().author != self.request.user:
            # Если нет-перенаправление на стр поста.
            return redirect('blog:post_detail', post_id=kwargs['post_id'])
        return super().dispatch(request, args, **kwargs)

    def get_context_data(self, **kwargs):
        # получить данные поста по первичному ключу.
        context = super().get_context_data(**kwargs)
        context['post'] = get_object_or_404(Post, pk=self.kwargs['post_id'])
        return context

    def get_success_url(self):
        username = self.request.user.username
        return reverse('blog:profile', kwargs={'username': username})


class CommentCreateView(LoginRequiredMixin, CreateView):
    post_data = None
    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'

    def dispatch(self, request, *args, **kwargs):
        # Проверить, есть ли в базе объект поста с переданным в запросе pk.
        self.post_data = get_object_or_404(Post, pk=kwargs['post_id'])
        return super().dispatch(request, args, **kwargs)

    def form_valid(self, form):
        # Переопределить поля формы,присвоив им значения
        # автора запроса(комментария) и комментируемого поста.
        form.instance.author = self.request.user
        form.instance.post = self.post_data
        return super().form_valid(form)

    def get_success_url(self):
        # После отправки коммента перенаправить пользователя на страницу поста
        return reverse(
            'blog:post_detail', kwargs={'post_id': self.post_data.pk}
        )


class CommentUpdateView(LoginRequiredMixin, UpdateView):
    post_data = None
    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'

    def dispatch(self, request, *args, **kwargs):
        # Проверить, является ли пользователь из запроса автором коммента.
        if self.get_object().author.username != self.request.user.username:
            # Если нет - перенаправить на страницу деталей поста.
            return redirect('blog:post_detail', post_id=kwargs['post_id'])
        # Если да - получить объект поста для дальнейшей работы.
        self.post_data = get_object_or_404(Post, id=kwargs['post_id'])
        return super().dispatch(request, args, **kwargs)

    def get_context_data(self, **kwargs):
        # получить данные комментария по первичному ключу.
        instance = get_object_or_404(Comment, pk=self.kwargs['comment_id'])
        form = CommentForm(instance=instance)
        context = super().get_context_data(**kwargs)
        context['form'] = form
        return context

    def form_valid(self, form):
        # Приcвоить полю author объект пользователя из запроса.
        form.instance.author = self.request.user
        # Приcвоить полю post объект публикации
        form.instance.post = self.post_data
        # Продолжить валидацию, описанную в форме
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            'blog:post_detail', kwargs={'post_id': self.post_data.pk})


class CommentDeleteView(LoginRequiredMixin, DeleteView):
    post_data = None
    model = Comment
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'

    def dispatch(self, request, *args, **kwargs):
        if self.get_object().author.username != self.request.user.username:
            return redirect('blog:post_detail', post_id=kwargs['post_id'])
        self.post_data = get_object_or_404(Post, id=kwargs['post_id'])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        # получить данные комментария по первичному ключу.
        context = super().get_context_data(**kwargs)
        context['comment'] = get_object_or_404(
            Comment, pk=self.kwargs['comment_id']
        )
        return context

    def get_success_url(self):
        return reverse(
            'blog:post_detail', kwargs={'post_id': self.post_data.pk}
        )
