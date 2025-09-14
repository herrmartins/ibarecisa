from django.db import models
from core.models import BaseModel
from users.models import CustomUser
from ckeditor.fields import RichTextField


class MinuteProjectModel(BaseModel):
    president = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, related_name="meet_president"
    )
    secretary = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, related_name="meet_secretary"
    )
    meeting_date = models.DateField()
    number_of_attendees = models.CharField(max_length=3)
    body = RichTextField(blank=True, null=True)

    class Meta:
        verbose_name = "Projeto de Ata"
        verbose_name_plural = "Projeto de Ata"

    def __str__(self):
        return f"Ata do dia {self.meeting_date}"

