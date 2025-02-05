from django.db import models
from core.models import BaseModel

class Composer(BaseModel):
    name = models.CharField(max_length=100)
    bio = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name
