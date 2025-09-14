from django import forms
from secretarial.models import MinuteProjectModel
from datetime import date
from users.models import CustomUser


class MinuteProjectModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(MinuteProjectModelForm, self).__init__(*args, **kwargs)

        self.fields["president"].queryset = CustomUser.objects.filter(is_pastor=True)
        self.fields["secretary"].queryset = CustomUser.objects.filter(is_secretary=True)

    class Meta:
        model = MinuteProjectModel
        fields = ["president", "secretary", "meeting_date", "number_of_attendees"]

        labels = {
            "meeting_date": "Data da assembléia",
            "number_of_attendees": "Número de presentes",
        }

        widgets = {
            "meeting_date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                    "value": date.today(),
                }
            ),
            "number_of_attendees": forms.TextInput(
                attrs={
                    "class": "form-control",
                }
            ),
        }

    president = forms.ModelChoiceField(
        queryset=CustomUser.objects.all(),
        widget=forms.Select(attrs={"class": "form-control"}),
        label="Presidente",
    )
    secretary = forms.ModelChoiceField(
        queryset=CustomUser.objects.all(),
        widget=forms.Select(attrs={"class": "form-control"}),
        label="Secretário",
    )


"""     president = forms.ModelChoiceField(
        queryset=CustomUser.objects.filter(
            functions__function__in=[UsersFunctions.Types.PASTOR, UsersFunctions.Types.MODERATOR]),
        widget=forms.Select(
            attrs={"class": "grid-item d-inline form-control my-2"}), label="Presidente",
    )
    secretary = forms.ModelChoiceField(
        queryset=CustomUser.objects.filter(
            functions__function=UsersFunctions.Types.SECRETARY),
        widget=forms.Select(
            attrs={"class": "grid-item d-inline form-control my-2"}), label="Secretário",
    )
    treasurer = forms.ModelChoiceField(
        queryset=CustomUser.objects.filter(
            functions__function=UsersFunctions.Types.TREASURER),
        widget=forms.Select(
            attrs={"class": "grid-item form-control my-2"}), label="Tesoureiro",
    )
    minute_reading_acceptance_proposal = forms.ModelChoiceField(
        queryset=CustomUser.objects.filter(type__in=[CustomUser.Types.STAFF, CustomUser.Types.REGULAR]).exclude(
            functions__function=UsersFunctions.Types.SECRETARY),
        widget=forms.Select(attrs={"class": "grid-item form-control my-2"}), label="Proposta de aceitação da ata",
    )

    minute_reading_acceptance_proposal_support = forms.ModelChoiceField(
        queryset=CustomUser.objects.filter(type__in=[CustomUser.Types.STAFF, CustomUser.Types.REGULAR]).exclude(
            functions__function=UsersFunctions.Types.SECRETARY),
        widget=forms.Select(attrs={"class": "grid-item form-control my-2"}), label="Apoio à proposta da ata",
    )

    finance_report_acceptance_proposal = forms.ModelChoiceField(
        queryset=CustomUser.objects.filter(type__in=[CustomUser.Types.STAFF, CustomUser.Types.REGULAR]).exclude(
            functions__function=UsersFunctions.Types.TREASURER),
        widget=forms.Select(attrs={"class": "grid-item d-inline form-control my-2"}), label="Proposta de aceitação do relatório financeiro",
    )

    finance_report_acceptance_proposal_support = forms.ModelChoiceField(
        queryset=CustomUser.objects.filter(type__in=[CustomUser.Types.STAFF, CustomUser.Types.REGULAR]).exclude(
            functions__function=UsersFunctions.Types.TREASURER),
        widget=forms.Select(attrs={"class": "grid-item form-control my-2"}), label="Apoio à proposta do relatório financeiro",
    ) """
