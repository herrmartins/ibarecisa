from core.models import BaseModel
from django.db import models


class Venue(BaseModel):
    name = models.CharField(max_length=100)
    address = models.TextField()
    capacity = models.PositiveIntegerField()

    def __str__(self):
        return self.name
