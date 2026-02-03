import logging
from django import forms
from blog.models import Post
from django.forms.widgets import HiddenInput

logger = logging.getLogger(__name__)


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
        logger.info(f"PostForm __init__ - author: {author}, args: {args}, kwargs keys: {list(kwargs.keys())}")
        super(PostForm, self).__init__(*args, **kwargs)
        instance = kwargs.get('instance')
        if author:
            self.fields['author'].initial = author
            self.fields['author'].required = False  # Don't require from POST, we'll set it in clean
            self.fields['author'].widget = HiddenInput()
        logger.info(f"PostForm __init__ - author initial: {self.fields['author'].initial}")
        if instance:
            self.fields['categories'].initial = instance.categories.all()

    def clean(self):
        cleaned_data = super().clean()
        logger.info(f"PostForm clean - cleaned_data keys: {list(cleaned_data.keys()) if cleaned_data else 'None'}")
        logger.info(f"PostForm clean - cleaned_data: {cleaned_data}")
        for field in self.fields:
            logger.info(f"PostForm clean - {field}: value={cleaned_data.get(field) if cleaned_data else 'N/A'}, errors={self.errors.get(field)}")
        return cleaned_data

    def clean_author(self):
        author = self.cleaned_data.get('author')
        logger.info(f"PostForm clean_author - author from cleaned_data: {author}")

        # Se author veio vazio do POST mas temos o initial, usa o initial
        if not author and self.fields['author'].initial:
            author = self.fields['author'].initial
            logger.info(f"PostForm clean_author - using initial author: {author}")
            self.cleaned_data['author'] = author

        if not author:
            logger.error("PostForm clean_author - author is None or empty!")
            raise forms.ValidationError("Este campo é obrigatório.")
        return author
