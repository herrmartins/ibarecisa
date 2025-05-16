from core.models import BaseModel
from django.db import models
from users.models import CustomUser
from ckeditor.fields import RichTextField
from secretarial.models import MeetingAgendaModel
from django.urls import reverse
import datetime


class MeetingMinuteModel(BaseModel):
    president = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="president")
    secretary = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="secretary")
    meeting_date = models.DateField(default=datetime.date.today)
    number_of_attendees = models.IntegerField(null=True, blank=True)
    body = RichTextField(blank=True, null=True)
    agenda = models.ManyToManyField(MeetingAgendaModel, blank=True)

    class Meta:
        verbose_name = "Ata"
        verbose_name_plural = "Atas"

    def get_absolute_url(self):
        return reverse("secretarial:minute-detail-view", kwargs={"pk": self.pk})

    def __str__(self):
        return f"Ata da reunião do dia {self.meeting_date}"
