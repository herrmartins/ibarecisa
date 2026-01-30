from django import forms
from django.forms import ModelForm
from secretarial.models import MeetingMinuteModel
from datetime import date
from users.models import CustomUser


class MinuteModelForm(ModelForm):
    body = forms.CharField(widget=forms.Textarea(attrs={"class": "w-full", "rows": 15}), label="Corpo do Texto")

    def __init__(self, *args, **kwargs):
        super(MinuteModelForm, self).__init__(*args, **kwargs)

        self.fields["president"].queryset = CustomUser.objects.filter(
            is_pastor=True)
        self.fields["secretary"].queryset = CustomUser.objects.filter(
            is_secretary=True)

        self.fields['meeting_date'].input_formats = [
            '%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y']

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
                    "class": "w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-all",
                }
            ),
            "secretary": forms.Select(
                attrs={
                    "class": "w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-all",
                }
            ),
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
            "agenda": forms.SelectMultiple(
                attrs={
                    "class": "w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-all",
                }
            ),
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
