from django import forms
# from django.core.exceptions import ValidationError
from users.models import CustomUser


class UpdateUserRoleModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(UpdateUserRoleModelForm, self).__init__(*args, **kwargs)
        self.fields['type'].widget.attrs['id'] = 'id_type'

    class Meta:
        model = CustomUser
        fields = ("type",)
        labels = {
            "type": "Status"
        }
        widgets = {
            "type": forms.Select(
                attrs={
                    "class": "grid-item d-inline form-control my-2",
                }
            ),
        }


"""     def clean(self):
        cleaned_data = super().clean()
        user_type = cleaned_data.get('type')
        functions = cleaned_data.get('functions')

        if user_type in (
            CustomUser.Types.CONGREGATED, CustomUser.Types.SIMPLE_USER
        ) and functions:
            raise ValidationError(
                "Congregados e usuários simples não podem ter função.") """
