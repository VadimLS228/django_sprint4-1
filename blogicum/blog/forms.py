from django import forms

from .models import Comment, Post, User


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        exclude = ("author",)
        widgets = {
            "pub_date": forms.DateTimeInput(
                attrs={"type": "datetime-local", "class": "form-control"},
                format=("%Y-%m-%d %H:%M:%S"),
            )
        }


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email")


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ("text",)
        widgets = {"text": forms.Textarea({"cols": "22", "rows": "5"})}
