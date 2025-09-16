from django.contrib import admin
from events.models import Event, Venue, EventCategory
import reversion
from reversion_compare.admin import CompareVersionAdmin

# Register models for versioning
reversion.register(Event)
reversion.register(Venue)
reversion.register(EventCategory)


@admin.register(Event)
class EventAdmin(CompareVersionAdmin):
    pass


@admin.register(Venue)
class VenueAdmin(CompareVersionAdmin):
    pass


@admin.register(EventCategory)
class EventCategoryAdmin(CompareVersionAdmin):
    pass
