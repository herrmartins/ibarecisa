from django import forms
from events.models import Venue


class VenueForm(forms.ModelForm):
    class Meta:
        model = Venue
        fields = ["name", "address", "capacity"]
        labels = {
            "name": "Nome",
            "address": "Endereço",
            "capacity": "Capacidade",
        }
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "address": forms.Textarea(attrs={"class": "form-control"}),
            "capacity": forms.NumberInput(attrs={"class": "form-control"}),
        }
