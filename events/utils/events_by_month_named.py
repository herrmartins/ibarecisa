from calendar import month_name
import locale
from events.models import Event


def events_by_month_named():
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')

    events_by_month = Event.objects.events_by_month_current_year()

    events_by_month_named = {}
    for month_num, events in events_by_month.items():
        # Evaluate the QuerySet and filter out empty or past events if needed
        evaluated_events = list(events)
        if evaluated_events:
            events_by_month_named[month_name[month_num]] = evaluated_events

    return events_by_month_named
