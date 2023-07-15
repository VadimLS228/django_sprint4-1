from django import forms

from .models import Comment, Post, User


class PostForm(forms.ModelForm):
    # Удаляем все описания полей.

    # Все настройки задаём в подклассе Meta.
    class Meta:
        # Указываем модель, на основе которой должна строиться форма.
        model = Post
        # Указываем, что надо отобразить все поля кроме автора.
        fields = (
            'image', 'title', 'text',
            'pub_date', 'location', 'category')
        widgets = {'pub_date': forms.DateTimeInput(
            attrs={'type': 'datetime-local', 'class': 'form-control'},
            format=('%Y-%m-%d %H:%M:%S'),)}


class ProfileForm(forms.ModelForm):

    class Meta:
        model = User
        fields = ('username', 'first_name',
                  'last_name', 'email')


class CommentForm(forms.ModelForm):

    class Meta:
        model = Comment
        fields = ('text',)
        widgets = {'text': forms.Textarea({'cols': '22', 'rows': '5'})}
