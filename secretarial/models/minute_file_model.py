from django.db import models
from core.models import BaseModel
from .minute_model import MeetingMinuteModel


class MinuteFileModel(BaseModel):
    minute = models.ForeignKey(
        MeetingMinuteModel,
        on_delete=models.CASCADE,
        related_name="attachments",
    )
    file = models.FileField(upload_to="minutes/attachments/")
    description = models.CharField(max_length=255, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Arquivo da Ata"
        verbose_name_plural = "Arquivos da Ata"

    def __str__(self):
        base = self.description or (self.file.name.split('/')[-1] if self.file else "Arquivo")
        return f"{base} (Ata #{self.minute_id})"
