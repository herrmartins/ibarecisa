from core.models import CustomUser
from events.models import Event
from django.db import models


class Schedule(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    date_time = models.DateTimeField()
    participants = models.ManyToManyField(CustomUser, through="ScheduleParticipant")
