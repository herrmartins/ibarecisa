from core.models import BaseModel
from django.db import models


class Hymnal(models.Model):
    title = models.CharField(max_length=200, unique=True)
    author = models.CharField(max_length=100, blank=True, null=True)
    theme = models.ForeignKey('SongTheme', on_delete=models.SET_NULL, null=True, blank=True)
    publication_date = models.DateField(blank=True, null=True)
    edition = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return f"{self.title}"
