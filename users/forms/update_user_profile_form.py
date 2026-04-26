from django import forms
from django.forms import ModelForm
from users.models import CustomUser
from django.forms.widgets import DateInput
from django.forms.widgets import ClearableFileInput
from django.core.exceptions import ValidationError
from datetime import date


class UpdateUserProfileModelForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def clean_date_of_birth(self):
        date_of_birth = self.cleaned_data.get("date_of_birth")
        if date_of_birth:
            if not isinstance(date_of_birth, date):
                raise ValidationError("Formato de data inválido. Use DD/MM/AAAA.")
        return date_of_birth

    def clean_baptism_date(self):
        baptism_date = self.cleaned_data.get("baptism_date")
        if baptism_date:
            if not isinstance(baptism_date, date):
                raise ValidationError("Formato de data inválido. Use DD/MM/AAAA.")
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
                    "class": "app-input",
                    "placeholder": "Prenome",
                }
            ),
            "last_name": forms.TextInput(
                attrs={
                    "class": "app-input",
                    "placeholder": "Sobrenome",
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "class": "app-input",
                    "placeholder": "E-mail",
                }
            ),
            "address": forms.TextInput(
                attrs={
                    "class": "app-input",
                    "placeholder": "Endereço",
                }
            ),
            "phone_number": forms.TextInput(
                attrs={
                    "class": "app-input",
                    "placeholder": "Phone",
                }
            ),
            "date_of_birth": DateInput(
                attrs={
                    "class": "datepicker app-input",
                    "type": "text",
                    "placeholder": "DD/MM/AAAA",
                },
                format='%d/%m/%Y'
            ),
            "about": forms.Textarea(
                attrs={
                    "class": "app-input",
                    "placeholder": "Sobre você...",
                },
            ),
            "profile_image": ClearableFileInput(
                attrs={
                    "class": "app-input",
                    "accept": "image/png, image/jpeg, image/jpg",
                }
            ),
            "cpf": forms.TextInput(
                attrs={
                    "class": "app-input",
                    "placeholder": "XXX.XXX.XXX-XX",
                }
            ),
            "baptism_date": DateInput(
                attrs={
                    "class": "datepicker app-input",
                    "type": "text",
                    "placeholder": "DD/MM/AAAA",
                },
                format='%d/%m/%Y'
            ),
        }
