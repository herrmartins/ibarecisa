from events.forms import VenueForm
from django.views.generic.edit import FormView
from django.contrib.auth.mixins import PermissionRequiredMixin
from events.models import Venue


class VenueFormView(PermissionRequiredMixin, FormView):
    permission_required = "events.add_event"
    template_name = 'events/venue_form.html'
    form_class = VenueForm
    success_url = '/events/venue/register/'

    def get_initial(self):
        venue_id = self.kwargs.get('pk')
        venue = Venue.objects.filter(id=venue_id).first()
        initial_data = super().get_initial()
        if venue:
            initial_data['name'] = venue.name
            initial_data['address'] = venue.address
            initial_data['capacity'] = venue.capacity
        return initial_data

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        venue_id = self.kwargs.get('pk')
        context["venue_id"] = venue_id
        return context
