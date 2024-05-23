from django import forms
from events.models import EventCategory


class EventCategoryForm(forms.ModelForm):
    class Meta:
        model = EventCategory
        fields = ["name", "description"]
        widgets = {
            "name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Nome da categoria"}
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Digite uma descrição...",
                }
            ),
        }
