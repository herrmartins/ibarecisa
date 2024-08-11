from users.models import CustomUser
from core.models import BaseModel
from django.db import models
from events.models import Event, Schedule


class ScheduleParticipant(BaseModel):
    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE)
    participant = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
