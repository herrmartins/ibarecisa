from django import forms
from blog.models import Category


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name']
        widgets = {
            'name': forms.TextInput(
                attrs={'class': 'app-input', 'placeholder': 'Nome da categoria'}),
        }
