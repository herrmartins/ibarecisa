from django import forms
from blog.models import Post
from ckeditor.widgets import CKEditorWidget
from django.forms.widgets import HiddenInput


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['author', 'title', 'content',
                  'summary', 'keywords', 'categories']
        labels = {
            "title": "Título",
            "content": "Conteúdo",
            "summary": "Resumo",
            "keywords": "Palavras Chave",
            "categories": "Categorias",
        }
        widgets = {
            'title': forms.TextInput(
                attrs={'class': 'form-control'}),
            'content': CKEditorWidget(),
            'summary': forms.TextInput(
                attrs={'class': 'form-control'}),
            'keywords': forms.TextInput(
                attrs={'class': 'form-control'}),
            'categories': forms.SelectMultiple(
                attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        author = kwargs.pop('author', None)
        super(PostForm, self).__init__(*args, **kwargs)
        instance = kwargs.get('instance')
        self.fields['author'].initial = author
        self.fields['author'].widget = HiddenInput()
        if instance:
            self.fields['categories'].initial = instance.categories.all()
