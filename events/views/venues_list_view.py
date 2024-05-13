from django.views.generic import ListView
from events.models import Venue


class VenuesListView(ListView):
    template_name = "events/venues_list.html"
    model = Venue
    context_object_name = "venues"
