from django.db import models
from core.modelsi import BaseModel


class ErrorRegistryModel(BaseModel):
    name = models.CharField(max_length=255)
    erro = models.TextField()
    date_time = models.DateTimeField("Data e hora do erro", auto_now_add=True)

    class Meta:
        verbose_name = "Registro de erros"
