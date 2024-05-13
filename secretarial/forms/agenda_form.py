from django import forms
from secretarial.models import MeetingAgendaModel


class MinuteAgendaModelForm(forms.ModelForm):
    class Meta:
        model = MeetingAgendaModel
        fields = ['agenda_title']

        labels = {
            "agenda_title": "Título",
        }

        widgets = {
            "agenda_title": forms.TextInput(
                attrs={
                    "class": "form-control",
                }
            ),
        }
