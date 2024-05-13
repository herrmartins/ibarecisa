from django.db import models
from core.models import BaseModel
from users.models import CustomUser
from ckeditor.fields import RichTextField
from secretarial.models import MeetingAgendaModel
from secretarial.utils.make_basic_minute_text import make_minute


class MinuteProjectModel(BaseModel):
    president = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, related_name="meet_president"
    )
    secretary = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, related_name="meet_secretary"
    )
    treasurer = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, related_name="meet_treasurer"
    )
    meeting_date = models.DateField()
    number_of_attendees = models.CharField(max_length=3)
    previous_minute_reading = models.BooleanField(default=True)
    minute_reading_acceptance_proposal = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, related_name="mr_acceptor", null=True
    )
    minute_reading_acceptance_proposal_support = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, related_name="mr_supporter", null=True
    )
    previous_finance_report_reading = models.BooleanField(default=True)
    finance_report_acceptance_proposal = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, related_name="fr_acceptor", null=True
    )
    finance_report_acceptance_proposal_support = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, related_name="fr_supporter", null=True
    )

    last_months_balance = models.DecimalField(decimal_places=2, max_digits=8)
    revenue = models.DecimalField(decimal_places=2, max_digits=8)
    expenses = models.DecimalField(decimal_places=2, max_digits=8)
    meeting_agenda = models.ManyToManyField(MeetingAgendaModel)
    body = RichTextField(blank=True, null=True)

    class Meta:
        verbose_name = "Projeto de Ata"
        verbose_name_plural = "Projeto de Ata"

    def __str__(self):
        return f"Ata do dia {self.meeting_date}"

    def create_basic_minute_text(self):
        data_dict = {
            "church": "Igreja Batista Regular de Cidade Satélite",
        }

        if self.president:
            president_name = f"{self.president.first_name} {self.president.last_name}"
            data_dict["president"] = president_name
        else:
            data_dict["president"] = "President Name Not Available"

        if self.secretary:
            secretary_name = f"{self.secretary.first_name} {self.secretary.last_name}"
            data_dict["secretary"] = secretary_name
        else:
            data_dict["secretary"] = "Secretary Name Not Available"

        if self.treasurer:
            treasurer_name = f"{self.secretary.first_name} {self.secretary.last_name}"
            data_dict["treasurer"] = secretary_name
        else:
            data_dict["treasurer"] = "treasurer Name Not Available"
        if self.minute_reading_acceptance_proposal and (
            self.minute_reading_acceptance_proposal.first_name
            or self.minute_reading_acceptance_proposal.last_name
        ):
            mr_acceptor_name = f"{self.minute_reading_acceptance_proposal.first_name} {self.minute_reading_acceptance_proposal.last_name}"
        else:
            mr_acceptor_name = "Minute Reading Acceptor Name Not Available"

        data_dict["minute_reading_acceptance_proposal"] = mr_acceptor_name

        # For minute_reading_acceptance_proposal_support
        if self.minute_reading_acceptance_proposal_support and (
            self.minute_reading_acceptance_proposal_support.first_name
            or self.minute_reading_acceptance_proposal_support.last_name
        ):
            mr_supporter_name = f"{self.minute_reading_acceptance_proposal_support.first_name} {self.minute_reading_acceptance_proposal_support.last_name}"
        else:
            mr_supporter_name = "Minute Reading Acceptor Supporter Name Not Available"

        data_dict["minute_reading_acceptance_proposal_support"] = mr_supporter_name

        # Similar logic can be applied to other fields...

        self.body = make_minute(data_dict)
        self.body = make_minute(data_dict)
