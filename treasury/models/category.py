from core.models import BaseModel
from django.db import models


class CategoryModel(BaseModel):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Categoria"
        verbose_name_plural = "Categorias"
