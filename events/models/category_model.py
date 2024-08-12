from django.db import models
from core.models import BaseModel


class EventCategory(BaseModel):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = 'Categoria'
        verbose_name_plural = "Categorias"

    def __str__(self):
        return self.name
