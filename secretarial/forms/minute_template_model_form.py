from django import forms
from secretarial.models import MinuteTemplateModel


class MinuteTemplateModelForm(forms.ModelForm):
    body = forms.CharField(widget=forms.Textarea(attrs={"class": "w-full", "rows": 15}), label="Texto")

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
                    "class": "w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-all",
                }
            ),
            "agenda": forms.SelectMultiple(
                attrs={
                    "class": "w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-all",
                }
            ),
        }
