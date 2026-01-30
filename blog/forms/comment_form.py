from django import forms
from blog.models import Comment


class CommentForm(forms.ModelForm):
    content = forms.CharField(widget=forms.Textarea(attrs={"class": "w-full", "rows": 8}), label="Conteúdo")

    class Meta:
        model = Comment
        fields = ['content']
