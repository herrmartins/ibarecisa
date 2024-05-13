from django.contrib import admin
from events.models import Event, Venue, EventCategory

admin.site.register(Event)
admin.site.register(Venue)
admin.site.register(EventCategory)
