import os
import uuid
from django.db import models
from core.models import BaseModel

class SongFile(BaseModel):
    FILE_TYPES = [
        ('audio', 'Áudio'),
        ('sheet', 'Partitura'),
        ('other', 'Outro'),
    ]

    song = models.ForeignKey('Song', on_delete=models.CASCADE, related_name='files')
    file = models.FileField(upload_to='song_files/')
    file_type = models.CharField(max_length=10, choices=FILE_TYPES)
    file_title = models.CharField(max_length=100, blank=True, null=True)
    description = models.CharField(max_length=255, blank=True, null=True)

    def save(self, *args, **kwargs):
        original_extension = os.path.splitext(self.file.name)[1]
        new_filename = f"{self.song.title}_{uuid.uuid4()}{original_extension}"
        
        self.file.name = f"{new_filename}"

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.song.title} - {self.get_file_type_display()}"
