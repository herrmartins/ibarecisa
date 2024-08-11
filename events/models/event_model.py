from django.db import models
from core.models import BaseModel
from users.models import CustomUser
from django.utils import timezone
from datetime import timedelta
from django.core.exceptions import ValidationError


class EventManager(models.Manager):
    def events_by_month_current_year(self):
        current_date = timezone.now()
        events_by_month = {}
        for month in range(1, 13):
            month_events = self.filter(
                start_date__year=current_date.year,
                start_date__month=month,
                end_date__gte=current_date,
            ) | self.filter(
                start_date__year=current_date.year,
                start_date__month=month,
                end_date__isnull=True,
                start_date__gte=current_date - timedelta(days=5),
            ).order_by(
                "start_date", "end_date"
            )
            events_by_month[month] = month_events
        return events_by_month


class Event(BaseModel):
    EVENT_TYPE_CHOICES = (
        ("permanent", "Permanent"),
        ("occasional", "Occasional"),
    )

    user = models.ForeignKey(
        CustomUser, on_delete=models.SET_DEFAULT, null=False, blank=False, default=1
    )
    title = models.CharField(max_length=100, null=False, blank=False)
    description = models.TextField(null=True, blank=True)
    start_date = models.DateTimeField(blank=False, null=False)
    end_date = models.DateTimeField(null=True, blank=True)
    price = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    location = models.ForeignKey(
        "events.Venue", on_delete=models.SET_DEFAULT, null=False, blank=False, default=1
    )
    contact_user = models.ForeignKey(
        "users.CustomUser",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="event_custom_user",
    )
    contact_name = models.CharField(max_length=100, null=True, blank=True)
    category = models.ForeignKey(
        "events.EventCategory", on_delete=models.PROTECT, null=True, blank=True
    )
    event_type = models.CharField(max_length=20, choices=EVENT_TYPE_CHOICES)
    recurrence_pattern = models.CharField(max_length=20, blank=True, null=True)
    default_day_of_week = models.IntegerField(null=True, blank=True)
    default_day_of_month = models.IntegerField(null=True, blank=True)

    objects = EventManager()

    def clean(self):
        # Check if the start_date is in the past
        if self.start_date and self.start_date < timezone.now():
            raise ValidationError(
                {"start_date": "The start date cannot be in the past."}
            )

    def __str__(self):
        return self.title
