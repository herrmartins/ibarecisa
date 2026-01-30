from django import forms
from blog.models import Post
from django.forms.widgets import HiddenInput


class PostForm(forms.ModelForm):
    content = forms.CharField(widget=forms.Textarea(attrs={"class": "w-full", "rows": 15}), label="Conteúdo")

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
                attrs={'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-all'}),
            'summary': forms.TextInput(
                attrs={'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-all'}),
            'keywords': forms.TextInput(
                attrs={'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-all'}),
            'categories': forms.SelectMultiple(
                attrs={'class': 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-all'}),
        }

    def __init__(self, *args, **kwargs):
        author = kwargs.pop('author', None)
        super(PostForm, self).__init__(*args, **kwargs)
        instance = kwargs.get('instance')
        self.fields['author'].initial = author
        self.fields['author'].widget = HiddenInput()
        if instance:
            self.fields['categories'].initial = instance.categories.all()
