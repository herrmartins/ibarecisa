from events.forms import EventForm
from django.views.generic.edit import FormView
from django.contrib.auth.mixins import PermissionRequiredMixin
from events.utils.events_by_month_named import events_by_month_named
from events.models import Event


class EventsFormView(PermissionRequiredMixin, FormView):
    permission_required = "events.add_event"
    template_name = "events/form.html"
    form_class = EventForm
    success_url = "/events/register/"
    context_object_name = "context_object"

    def get_initial(self):
        event_id = self.kwargs.get("pk")
        event = Event.objects.filter(id=event_id).first()
        initial_data = super().get_initial()
        if event:
            initial_data["title"] = event.title
            initial_data["description"] = event.description
            initial_data["start_date"] = event.start_date
            initial_data["end_date"] = event.end_date
            initial_data["price"] = event.price
            initial_data["location"] = event.location
            initial_data["contact_user"] = event.contact_user
            initial_data["contact_name"] = event.contact_name
            initial_data["category"] = event.category
        return initial_data

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["events"] = events_by_month_named()
        event_pk = self.kwargs.get("pk")
        if event_pk:
            context["current_event"] = Event.objects.get(pk=event_pk)
        return context
