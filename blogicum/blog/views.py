from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Count
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import (CreateView, DeleteView, DetailView, ListView,
                                  UpdateView)

from .forms import CommentForm, PostForm
from .models import Category, Post, Comment


User = get_user_model()

NEW_POSTS = 5


@login_required
def simple_view(request):
    return HttpResponse('Страница для залогиненных пользователей!')


'''
@login_required
def add_comment(request, pk):
    # Получаем публикацию или выбрасываем 404 ошибку.
    post = get_object_or_404(Post, pk=pk)
    # Функция должна обрабатывать только POST-запросы.
    form = CommentForm(request.POST)
    if form.is_valid():
        # Создаём объект комментария, но не сохраняем его в БД.
        comment = form.save(commit=False)
        # В поле author передаём объект автора коммента.
        comment.author = request.user
        # В поле поста передаём объект поста.
        comment.post = post
        # Сохраняем объект в БД.
        comment.save()
    # Перенаправляем пользователя назад, на страницу поста.
    return redirect('post:detail', pk=pk)
'''


class HelpList(ListView):
    """
    Вспомогательный CBV:
    возвращает публикации, сделанные до текущего момента времени
    соответственно запросу по автору, месту и категории.
    """

    model = Post
    paginate_by = 10
    ordering = '-pub_date'

    # Получаем список постов в соотв-ии с авторм/местом/категорией.
    # Фильтруем только опубликованные.

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.select_related(
            'author', 'location', 'category'
        ).filter(is_published=True,
                 category__is_published=True,
                 pub_date__lte=timezone.now()
                 ).annotate(comment_count=Count('comments'))


class PostListView(HelpList, ListView):
    '''Отображение списка постов на главной странице.'''

    template_name = 'blog/index.html'


class CategoryListView(HelpList, ListView):
    '''Отображение списка постов конкретной категории.'''

    template_name = 'blog/category.html'
    model = Category

    # Получаем список постов в соотв-ии с категорией.
    def get_queryset(self):
        self.category = get_object_or_404(
            Category, slug=self.kwargs['category_slug'], is_published=True)
        return super().get_queryset().filter(category=self.category)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        return context


class ProfileDetailView(HelpList, ListView):
    '''Отображение страницы конкретного пользователя со всеми его постами.'''
    template_name = 'blog/profile.html'

    def get_queryset(self, *args, **kwargs):
        return super().get_queryset(*args, **kwargs).filter(
            author=self.kwargs['username']
        )

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['profile'] = get_object_or_404(
            get_user_model(),
            username=self.kwargs['username']
        )
        return context


class PostDetailView(DetailView):
    '''Отображение отдельного поста.'''
    # Используемая модель.
    model = Post
    template_name = 'blog/detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Записываем в переменную form пустой объект формы.
        context['form'] = CommentForm()
        # Запрашиваем все комменты для выбранного поста
        context['comments'] = self.object.comments.select_related('author')
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

    def dispatch(self, request, *args, **kwargs):
        # При получении объекта не указываем автора.
        # Результат сохраняем в переменную.
        instance = get_object_or_404(Post, pk=kwargs['pk'])
        # Сверяем автора объекта и пользователя из запроса.
        if instance.author != request.user:
            # Здесь может быть вызов ошибки,или редирект на нужную страницу.
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    template_name = 'blog/user.html'

    def get_success_url(self):
        return reverse('blog:profile', args=(self.request.user.username,))

    def form_valid(self, form):
        return super().form_valid(form)


class PostDeleteView(LoginRequiredMixin, DeleteView):
    model = Post
    success_url = reverse_lazy('blog:profile')

    def dispatch(self, request, *args, **kwargs):
        # При получении объекта не указываем автора.
        # Результат сохраняем в переменную.
        instance = get_object_or_404(Post, pk=kwargs['pk'])
        # Сверяем автора объекта и пользователя из запроса.
        if instance.author != request.user:
            # Здесь может быть вызов ошибки,или редирект на нужную страницу.
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class CommentCreateView(LoginRequiredMixin, CreateView):

    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'

    def dispatch(self, request, *args, **kwargs):
        self.post_obj = get_object_or_404(Post, pk=kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.post_id = self.post_obj
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('blog:post_detail',
                       kwargs={'post_id': self.post_obj.pk})


class CommentUpdateView(LoginRequiredMixin, UpdateView):
    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'
    post_data = None
    pk_url_kwarg = 'comment_id'

    def dispatch(self, request, *args, **kwargs):
        if self.get_object().author != self.request.user:
            return redirect('blog:post_detail', pk=self.kwargs['pk'])
        self.post_data = get_object_or_404(Post, pk=kwargs['pk'])
        return super().dispatch(request, args, **kwargs)

    def get_success_url(self):
        pk = self.post_data.pk
        return reverse('blog:post_detail', kwargs={'post_id': pk})


class CommentDeleteView(LoginRequiredMixin, DeleteView):
    model = Comment
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'

    def dispatch(self, request, *args, **kwargs):
        if self.get_object().author != self.request.user:
            return redirect('blog:post_detail', pk=self.kwargs['pk'])
        self.post_data = get_object_or_404(Post, pk=kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        pk = self.post_data.pk
        return reverse('blog:post_detail',
                       kwargs={'post_id': pk})
