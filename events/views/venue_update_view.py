from django.views.generic.edit import UpdateView
from events.models import Venue
from events.forms import VenueForm
from django.urls import reverse_lazy
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
import reversion


class VenueUpdateView(PermissionRequiredMixin, SuccessMessageMixin, UpdateView):
    permission_required = "events.add_event"
    model = Venue
    form_class = VenueForm
    template_name = 'events/venue_form.html'
    success_url = reverse_lazy('events:venues-list')
    success_message = "Local de eventos alterado com sucesso..."

    def form_valid(self, form):
        with reversion.create_revision():
            reversion.set_user(self.request.user)
            return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Erro no formulário...")
        return super().form_invalid(form)
