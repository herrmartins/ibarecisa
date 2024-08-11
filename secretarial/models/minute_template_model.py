from core.models import BaseModel
from django.db import models
from ckeditor.fields import RichTextField
from secretarial.models import MeetingAgendaModel
from django.urls import reverse


class MinuteTemplateModel(BaseModel):
    title = models.CharField(max_length=255)
    body = RichTextField(blank=True, null=True)
    agenda = models.ManyToManyField(MeetingAgendaModel, blank=True)

    class Meta:
        verbose_name = "Modelo de Ata"
        verbose_name_plural = "Modelos de Ata"

    def get_absolute_url(self):
        return reverse("secretarial:minute-home")

    def __str__(self):
        return self.title
