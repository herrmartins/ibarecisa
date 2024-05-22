from django import forms
from treasury.models import CategoryModel


class CategoryModelForm(forms.ModelForm):
    class Meta:
        model = CategoryModel
        fields = ["name"]
        labels = {"name": "Nome"}
        widgets = {"name": forms.TextInput(attrs={"class": "form-control"})}
