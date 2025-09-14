import uuid

from django import forms
from django.core.exceptions import ValidationError
from users.models import CustomUser


class MemberRegistrationForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
            "date_of_birth",
            "phone_number",
            "cpf",
            "baptism_date",
            "address",
            "about",
            "type",
        ]
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control"}),
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "date_of_birth": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "phone_number": forms.TextInput(attrs={"class": "form-control"}),
            "cpf": forms.TextInput(attrs={"class": "form-control"}),
            "baptism_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "address": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "about": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "type": forms.Select(attrs={"class": "form-control"}),
        }
        labels = {
            "username": "Nome do usuário",
            "first_name": "Nome",
            "last_name": "Sobrenome",
            "email": "E-mail",
            "date_of_birth": "Data de nascimento",
            "phone_number": "Telefone",
            "cpf": "CPF",
            "baptism_date": "Data do batismo",
            "address": "Endereço",
            "about": "Sobre",
            "type": "Tipo",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].required = True
        self.fields["first_name"].required = True
        self.fields["last_name"].required = True

        self.fields["email"].required = False
        self.fields["date_of_birth"].required = False
        self.fields["phone_number"].required = False
        self.fields["cpf"].required = False
        self.fields["baptism_date"].required = False
        self.fields["address"].required = False
        self.fields["about"].required = False
        self.fields["type"].required = False

        if not self.instance.pk:
            self.fields["type"].initial = CustomUser.Types.REGULAR

    def save(self, commit=True):
        user = super().save(commit=False)
        if not user.email:
            user.email = f"no-email+{uuid.uuid4().hex}@example.com"
        user.set_unusable_password()
        if commit:
            user.save()
        return user