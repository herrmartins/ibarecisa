from django import forms
from users.models import CustomUser


class UserQualifyingForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ["is_pastor", "is_secretary", "is_treasurer"]
        widgets = {
            "is_pastor": forms.CheckboxInput(attrs={"class": "form-check-input d-block"}),
            "is_secretary": forms.CheckboxInput(attrs={"class": "form-check-input d-block"}),
            "is_treasurer": forms.CheckboxInput(attrs={"class": "form-check-input d-block"}),
        }
        labels = {
            "is_pastor": "Pastor",
            "is_secretary": "Secretário",
            "is_treasurer": "Tesoureiro",
        }
