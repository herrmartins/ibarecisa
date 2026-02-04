from django import forms
from events.models import EventCategory


class EventCategoryForm(forms.ModelForm):
    class Meta:
        model = EventCategory
        fields = ["name", "description"]
        widgets = {
            "name": forms.TextInput(
                attrs={"class": "app-input", "placeholder": "Nome da categoria"}
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "app-input",
                    "rows": 4,
                    "placeholder": "Digite uma descrição...",
                }
            ),
        }
