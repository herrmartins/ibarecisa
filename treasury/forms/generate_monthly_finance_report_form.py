from django import forms
from treasury.models import (
    MonthlyBalance,
    MonthlyReportModel,
    MonthlyTransactionByCategoryModel,
)


class GenerateFinanceReportModelForm(forms.ModelForm):
    class Meta:
        model = MonthlyReportModel
        fields = "__all__"
        exclude = ("ativo",)

        labels = {
            "month": "Mês:",
            "previous_month_balance": "Saldo do mês anterior:",
            "total_positive_transactions": "Total de transações positivas:",
            "total_negative_transactions": "Total de transações negativas:",
            "in_cash": "Em dinheiro:",
            "in_current_account": "Na conta corrente:",
            "in_savings_account": "Na conta poupança:",
            "monthly_result": "Resultado mensal:",
            "total_balance": "Saldo:",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["month"].widget = forms.HiddenInput()
        self.fields["previous_month_balance"].widget = forms.NumberInput(
            attrs={"class": "form-control bg-light", "readonly": True}
        )
        self.fields["total_positive_transactions"].widget = forms.NumberInput(
            attrs={"class": "form-control bg-light", "readonly": True}
        )
        self.fields["total_negative_transactions"].widget = forms.NumberInput(
            attrs={"class": "form-control bg-light", "readonly": True}
        )
        self.fields["in_cash"].widget = forms.TextInput(
            attrs={"class": "form-control", "type": "number", "step": "0.01"}
        )
        self.fields["in_current_account"].widget = forms.TextInput(
            attrs={"class": "form-control", "type": "number", "step": "0.01"}
        )
        self.fields["in_savings_account"].widget = forms.TextInput(
            attrs={"class": "form-control", "type": "number", "step": "0.01"}
        )
        self.fields["monthly_result"].widget = forms.NumberInput(
            attrs={"class": "form-control bg-light", "readonly": True}
        )
        self.fields["total_balance"].widget = forms.NumberInput(
            attrs={"class": "form-control bg-light", "readonly": True}
        )

        initial_date = self.initial.get("month")
        if initial_date:
            self.initial["month"] = initial_date.strftime("%Y-%m-%d")
