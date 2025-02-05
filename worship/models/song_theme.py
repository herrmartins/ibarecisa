from django.db import models
from core.models import BaseModel

class SongTheme(BaseModel):
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.title