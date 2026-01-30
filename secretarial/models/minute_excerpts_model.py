from django.db import models
from core.models import BaseModel
from django.urls import reverse


class MinuteExcerptsModel(BaseModel):
    title = models.CharField(max_length=100)
    excerpt = models.TextField(blank=True)
    times_used = models.IntegerField(default=1)

    class Meta:
        verbose_name = "Trecho de Atas"
        verbose_name_plural = "Trechos de Atas"

    def get_absolute_url(self):
        return reverse("secretarial:excerpt-detail", kwargs={"pk": self.pk})

    def __str__(self):
        return self.title
