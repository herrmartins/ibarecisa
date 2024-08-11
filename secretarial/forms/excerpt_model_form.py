from django import forms
from secretarial.models import MinuteExcerptsModel
from ckeditor.widgets import CKEditorWidget


class MinuteExcerptsModelForm(forms.ModelForm):
    class Meta:
        model = MinuteExcerptsModel
        fields = ["title", "excerpt"]

        labels = {
            "title": "Título",
            "excerpt": "Trecho",
        }

        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": "form-control",
                }
            ),
            "excerpt": CKEditorWidget(),
            "agenda": forms.SelectMultiple(
                attrs={
                    "class": "grid-item d-inline form-control my-2",
                }
            ),
        }
