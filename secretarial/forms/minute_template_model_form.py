from django import forms
from secretarial.models import MinuteTemplateModel
from ckeditor.widgets import CKEditorWidget


class MinuteTemplateModelForm(forms.ModelForm):
    class Meta:
        model = MinuteTemplateModel
        fields = ["title", "body", "agenda"]
        labels = {
            "title": "Título",
            "body": "Texto",
            "agenda": "Assuntos",
        }

        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": "form-control my-2",
                    "placeholder": "Digite o critério de busca...",
                }
            ),
            "body": CKEditorWidget(),
            "agenda": forms.SelectMultiple(
                attrs={
                    "class": "grid-item d-inline form-control my-2",
                }
            ),
        }
