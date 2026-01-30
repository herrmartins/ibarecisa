from django import forms
from secretarial.models import MinuteProjectModel
from users.models import CustomUser
from datetime import date


class MinuteProjectEditForm(forms.ModelForm):
    body = forms.CharField(widget=forms.Textarea(attrs={"class": "w-full", "rows": 15}), label="Texto da ata")

    def __init__(self, *args, **kwargs):
        super(MinuteProjectEditForm, self).__init__(*args, **kwargs)

        self.fields["president"].queryset = CustomUser.objects.filter(
            is_pastor=True)
        self.fields["secretary"].queryset = CustomUser.objects.filter(
            is_secretary=True)

        self.fields['meeting_date'].input_formats = [
            '%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y']

    class Meta:
        model = MinuteProjectModel
        fields = ["meeting_date", "number_of_attendees",
                  "president", "secretary", "body"]
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
                    "class": "w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-all",
                    "type": "text",
                    "placeholder": "DD/MM/YYYY",
                },
                format='%d/%m/%Y'
            ),
            "number_of_attendees": forms.TextInput(
                attrs={
                    "class": "w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-all",
                }
            ),
            "president": forms.Select(attrs={"class": "w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-all"}),
            "secretary": forms.Select(attrs={"class": "w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-all"}),
        }

    president = forms.ModelChoiceField(
        queryset=CustomUser.objects.all(),
        widget=forms.Select(attrs={
                            "class": "w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-all"}),
        label="Presidente",
    )
    secretary = forms.ModelChoiceField(
        queryset=CustomUser.objects.all(),
        widget=forms.Select(attrs={
                            "class": "w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-all"}),
        label="Secretário",
    )
