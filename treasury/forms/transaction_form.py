from django import forms
from treasury.models import TransactionModel
from django.forms.widgets import HiddenInput, FileInput


class TransactionForm(forms.ModelForm):
    class Meta:
        model = TransactionModel
        fields = [
            "user",
            "category",
            "description",
            "amount",
            "date",
            "acquittance_doc",
        ]

        fields = [
            "user",
            "category",
            "description",
            "amount",
            "date",
            "acquittance_doc",
        ]

        labels = {
            "category": "Categoria",
            "description": "Descrição",
            "amount": "Valor",
            "date": "Data",
            "acquittance_doc": "Recibo",
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super(TransactionForm, self).__init__(*args, **kwargs)
        self.fields["user"].initial = user
        self.fields["user"].widget = HiddenInput()

        self.fields["category"].widget.attrs["class"] = "form-select"
        self.fields["description"].widget.attrs["class"] = "form-control"
        self.fields["amount"].widget.attrs["class"] = "form-control"
        self.fields["date"].widget = forms.DateInput(
            attrs={"class": "form-control", "type": "date"}
        )
        self.fields["acquittance_doc"].widget = FileInput(
            attrs={"class": "form-control", "accept": "image/jpeg,image/png"}
        )

        initial_date = self.initial.get("date")
        if initial_date:
            self.initial["date"] = initial_date.strftime("%Y-%m-%d")
