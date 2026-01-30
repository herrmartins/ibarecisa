from django import forms
from django.forms import ModelForm
from secretarial.models import MeetingMinuteModel
from datetime import date
from users.models import CustomUser


class MinuteModelForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(MinuteModelForm, self).__init__(*args, **kwargs)

        self.fields["president"].queryset = CustomUser.objects.filter(
            is_pastor=True)
        self.fields["secretary"].queryset = CustomUser.objects.filter(
            is_secretary=True)

    class Meta:
        model = MeetingMinuteModel
        fields = (
            "president",
            "secretary",
            "meeting_date",
            "number_of_attendees",
            "body",
            "agenda",
        )
        labels = {
            "president": "Presidente",
            "secretary": "Secretário",
            "meeting_date": "Data da Reunião",
            "number_of_attendees": "Número de presentes",
            "body": "Corpo do Texto",
            "agenda": "Pauta",
        }
        widgets = {
            "president": forms.Select(
                attrs={
                    "class": "grid-item d-inline form-control my-2",
                }
            ),
            "secretary": forms.Select(
                attrs={
                    "class": "grid-item d-inline form-control my-2",
                }
            ),
            "meeting_date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                    "value": date.today(),
                }
            ),
            "number_of_attendees": forms.TextInput(
                attrs={
                    "class": "form-control",
                }
            ),
            "body": forms.HiddenInput(),
            "agenda": forms.SelectMultiple(
                attrs={
                    "class": "grid-item d-inline form-control my-2",
                }
            ),
        }
