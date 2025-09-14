from django import forms
from secretarial.models import MinuteProjectModel
from users.models import CustomUser
from datetime import date


class MinuteProjectEditForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(MinuteProjectEditForm, self).__init__(*args, **kwargs)

        # Filtrar apenas pastores e secretários
        self.fields["president"].queryset = CustomUser.objects.filter(is_pastor=True)
        self.fields["secretary"].queryset = CustomUser.objects.filter(is_secretary=True)

    class Meta:
        model = MinuteProjectModel
        fields = ["meeting_date", "number_of_attendees", "president", "secretary", "body"]
        exclude = []

        labels = {
            "meeting_date": "Data da assembleia",
            "number_of_attendees": "Número de presentes",
            "president": "Presidente",
            "secretary": "Secretário",
            "body": "Texto da ata",
        }

        widgets = {
            "meeting_date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),
            "number_of_attendees": forms.TextInput(
                attrs={
                    "class": "form-control",
                }
            ),
            "president": forms.Select(attrs={"class": "form-control"}),
            "secretary": forms.Select(attrs={"class": "form-control"}),
            "body": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 15,
                }
            ),
        }

    president = forms.ModelChoiceField(
        queryset=CustomUser.objects.all(),
        widget=forms.Select(attrs={"class": "form-control"}),
        label="Presidente",
    )
    secretary = forms.ModelChoiceField(
        queryset=CustomUser.objects.all(),
        widget=forms.Select(attrs={"class": "form-control"}),
        label="Secretário",
    )