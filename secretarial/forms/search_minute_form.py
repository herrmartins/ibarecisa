from django import forms
from datetime import date
from dateutil.relativedelta import relativedelta


class SearchMinuteForm(forms.Form):
    search_field = forms.CharField(
        label="",
        required=True,
        max_length=100,
        widget=forms.TextInput(
            attrs={
                "class": "form-control my-2",
                "placeholder": "Digite o critério de busca...",
            }
        ),
    )
    start_date = forms.DateField(
        label="Data inicial",
        initial=date.today() + relativedelta(months=-6),
        widget=forms.DateInput(
            attrs={
                "class": "datepicker form-control",
                "type": "text",
                "placeholder": "DD/MM/AAAA",
            },
            format='%d/%m/%Y'
        ),
    )

    end_date = forms.DateField(
        label="Data final",
        initial=date.today(),
        widget=forms.DateInput(
            attrs={
                "class": "datepicker form-control",
                "type": "text",
                "placeholder": "DD/MM/AAAA",
            },
            format='%d/%m/%Y'
        ),
    )
    start_date = forms.DateField(
        label="Data inicial",
        widget=forms.DateInput(
            attrs={
                "class": "form-control",
                "type": "date",
                "value": date.today() - relativedelta(months=-6),
            }
        ),
    )

    end_date = forms.DateField(
        label="Data final",
        widget=forms.DateInput(
            attrs={
                "class": "form-control",
                "type": "date",
                "value": date.today(),
            }),)
