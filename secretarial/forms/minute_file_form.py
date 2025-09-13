from django import forms
from django.forms import ModelForm
from secretarial.models import MinuteFileModel


class MinuteFileModelForm(ModelForm):
    class Meta:
        model = MinuteFileModel
        fields = (
            "file",
            "description",
        )
        labels = {
            "file": "Arquivo",
            "description": "Descrição (opcional)",
        }
        widgets = {
            "file": forms.ClearableFileInput(
                attrs={"class": "form-control"}
            ),
            "description": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Descrição"}
            ),
        }
