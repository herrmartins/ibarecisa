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
            'title': forms.TextInput(attrs={'class': 'app-input', 'placeholder': 'Título do post'}),
            'summary': forms.TextInput(attrs={'class': 'app-input', 'placeholder': 'Resumo breve do post'}),
            'keywords': forms.TextInput(attrs={'class': 'app-input', 'placeholder': 'palavra1, palavra2, palavra3'}),
            'categories': forms.SelectMultiple(attrs={'class': 'app-input'}),
        }

    def __init__(self, *args, **kwargs):
        author = kwargs.pop('author', None)
        super(PostForm, self).__init__(*args, **kwargs)
        instance = kwargs.get('instance')
        self.fields['author'].initial = author
        self.fields['author'].widget = HiddenInput()
        if instance:
            self.fields['categories'].initial = instance.categories.all()
