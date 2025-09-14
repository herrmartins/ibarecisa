from django import forms
from secretarial.models import MinuteProjectModel
from datetime import date
from users.models import CustomUser


class MinuteProjectModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(MinuteProjectModelForm, self).__init__(*args, **kwargs)

        self.fields["president"].queryset = CustomUser.objects.filter(is_pastor=True)
        self.fields["secretary"].queryset = CustomUser.objects.filter(is_secretary=True)

        # Garantir formatos de entrada para a data
        self.fields['meeting_date'].input_formats = ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y']

    class Meta:
        model = MinuteProjectModel
        fields = ["president", "secretary", "meeting_date", "number_of_attendees"]

        labels = {
            "meeting_date": "Data da assembléia",
            "number_of_attendees": "Número de presentes",
        }

        widgets = {
            "meeting_date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "text",
                    "placeholder": "DD/MM/YYYY",
                    "value": date.today().strftime('%d/%m/%Y'),
                },
                format='%d/%m/%Y'
            ),
            "number_of_attendees": forms.TextInput(
                attrs={
                    "class": "form-control",
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
