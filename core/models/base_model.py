from django.db import models
from datetime import datetime


class BaseModel(models.Model):
    created = models.DateField(
        "Data de Criação", auto_now_add=True)
    modified = models.DateField(
        "Data de Atualização", auto_now_add=True)
    ativo = models.BooleanField("Ativo?", default=True)

    class Meta:
        abstract = True
