from django import forms
from treasury.models import MonthlyBalance


class InitialBalanceForm(forms.ModelForm):
    class Meta:
        model = MonthlyBalance
        fields = ["balance", "month", "is_first_month"]

    balance = forms.DecimalField(
        label="Saldo Inicial",
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )

    month = forms.DateField(
        label="Selecione o mês e ano",
        widget=forms.DateInput(attrs={"type": "month", "class": "form-control"}),
        input_formats=["%Y-%m"],
    )

    is_first_month = forms.BooleanField(
        widget=forms.HiddenInput(attrs={"value": "True"}), required=False
    )

    def clean(self):
        cleaned_data = super().clean()
        month = cleaned_data.get("month")
        if month is not None and (month.month < 1 or month.month > 12):
            raise forms.ValidationError("Month must be between 1 and 12.")

        return cleaned_data
