from django import forms
from django.forms import ModelForm
from users.models import CustomUser
from django.forms.widgets import DateInput
from django.forms.widgets import ClearableFileInput
from django.core.exceptions import ValidationError
from datetime import datetime, date


class UpdateUserProfileModelForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        initial_date = self.initial.get("date_of_birth")
        if initial_date:
            self.initial["date_of_birth"] = initial_date.strftime("%Y-%m-%d")

        initial_baptism_date = self.initial.get("baptism_date")
        if initial_baptism_date:
            self.initial["baptism_date"] = initial_baptism_date.strftime("%Y-%m-%d")

    def clean_date_of_birth(self):
        date_of_birth = self.cleaned_data.get("date_of_birth")
        if date_of_birth:
            if isinstance(date_of_birth, date):  # Using the imported 'date' from datetime module
                date_of_birth = date_of_birth.strftime("%Y-%m-%d")

            try:
                datetime.strptime(date_of_birth, "%Y-%m-%d")
            except ValueError:
                raise ValidationError("Invalid date format. Please use YYYY-MM-DD.")
        return date_of_birth


    def clean_baptism_date(self):
        baptism_date = self.cleaned_data.get("baptism_date")
        if baptism_date:
            if isinstance(baptism_date, date):
                baptism_date = baptism_date.strftime("%Y-%m-%d")

            try:
                datetime.strptime(baptism_date, "%Y-%m-%d")
            except ValueError:
                raise ValidationError("Invalid date format. Please use YYYY-MM-DD.")
        return baptism_date
    
    def clean_profile_image(self):
        profile_image = self.cleaned_data.get('profile_image')
        if profile_image:
            if not profile_image.name.endswith(('.png', '.jpg', '.jpeg', '.JPEG', '.JPG', '.PNG')):
                raise ValidationError('Invalid file type. Only PNG, JPG, and JPEG files are allowed.')
        return profile_image


    class Meta:
        model = CustomUser
        fields = (
            "first_name",
            "last_name",
            "email",
            "address",
            "phone_number",
            "is_whatsapp",
            "date_of_birth",
            "about",
            "profile_image",
            "cpf",
            "baptism_date",
        )

        labels = {
            "first_name": "",
            "last_name": "",
            "email": "",
            "address": "",
            "phone_number": "",
            "is_whatsapp": "Whatsapp?",
            "date_of_birth": "",
            "about": "",
            "profile_image": "Foto do Perfil",
            "cpf": "CPF",
            "baptism_date": "Data do batismo",
        }

        widgets = {
            "first_name": forms.TextInput(
                attrs={
                    "class": "form-control my-2",
                    "placeholder": "Prenome",
                }
            ),
            "last_name": forms.TextInput(
                attrs={
                    "class": "form-control my-2",
                    "placeholder": "Sobrenome",
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "class": "form-control my-2",
                    "placeholder": "E-mail",
                }
            ),
            "address": forms.TextInput(
                attrs={
                    "class": "form-control my-2",
                    "placeholder": "Endereço",
                }
            ),
            "phone_number": forms.TextInput(
                attrs={
                    "class": "form-control my-2",
                    "placeholder": "Phone",
                }
            ),
            "date_of_birth": DateInput(
                attrs={
                    "class": "datepicker form-control",
                    "type": "date",
                },
            ),
            "about": forms.Textarea(
                attrs={
                    "class": "form-control my-2",
                    "placeholder": "Sobre você...",
                },
            ),
            "profile_image": ClearableFileInput(
                attrs={
                    "class": "form-control mt-2",
                    "accept": "image/png, image/jpeg, image/jpg",
                }
            ),
            "cpf": forms.TextInput(
                attrs={
                    "class": "form-control my-2",
                    "placeholder": "XXX.XXX.XXX-XX",
                }
            ),
            "baptism_date": DateInput(
                attrs={
                    "class": "datepicker form-control",
                    "type": "date",
                },
            ),
        }
