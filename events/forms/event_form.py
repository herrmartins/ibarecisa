from django import forms
from events.models import Event
from users.models import CustomUser
from django.core.exceptions import ValidationError
from django.utils import timezone


class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = [
            "title",
            "description",
            "start_date",
            "end_date",
            "price",
            "location",
            "contact_user",
            "contact_name",
            "category",
        ]
        labels = {
            "start_date": "Início",
            "end_date": "Final",
            "price": "Preço",
            "contact_name": "Contato",
            "contact_user": "Contato",
            "title": "Título",
            "description": "Descrição",
            "location": "Local",
            "category": "Categoria",
        }
        widgets = {
            "user": forms.HiddenInput(),
            "start_date": forms.DateTimeInput(
                attrs={"class": "datepicker app-input", 'type': 'text', 'placeholder': 'DD/MM/AAAA HH:MM'},
                format='%d/%m/%Y %H:%M'),
            "end_date": forms.DateTimeInput(
                attrs={"class": "datepicker app-input", 'type': 'text', 'placeholder': 'DD/MM/AAAA HH:MM'},
                format='%d/%m/%Y %H:%M'),
            "price": forms.NumberInput(attrs={"class": "app-input"}),
            "contact_name": forms.TextInput(attrs={"class": "app-input"}),
            "contact_user": forms.Select(attrs={"class": "app-input"}),
            "title": forms.TextInput(attrs={"class": "app-input"}),
            "description": forms.Textarea(
                attrs={"class": "app-input", "rows": 3}),
            "location": forms.Select(attrs={"class": "app-input"}),
            "category": forms.Select(attrs={"class": "app-input"}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super(EventForm, self).__init__(*args, **kwargs)
        if user is not None:
            self.fields["user"] = forms.ModelChoiceField(
                queryset=CustomUser.objects.filter(pk=user.pk),
                empty_label=None,
                initial=user,
            )
            self.fields["user"].widget = forms.HiddenInput()

    def clean_start_date(self):
        start_date = self.cleaned_data.get("start_date")
        if start_date and start_date < timezone.now():
            raise ValidationError('A data não pode ser passada')
        return start_date

    def clean_end_date(self):
        end_date = self.cleaned_data.get("end_date")
        return end_date

    def clean(self):
        cleaned_data = super().clean()
        contact_name = cleaned_data.get("contact_name")
        custom_user = cleaned_data.get("contact_user")

        if not contact_name and not custom_user:
            self.add_error(
                "contact_name", "Please provide contact information.")
            raise forms.ValidationError("Please provide contact information.")

        if contact_name and custom_user:
            # Instead of raising an error, prioritize custom_user as contact
            cleaned_data["contact_user"] = custom_user
            cleaned_data["contact_name"] = ""

        return cleaned_data
