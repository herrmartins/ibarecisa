from django.views.generic.edit import CreateView
from events.models import Event
from django.urls import reverse_lazy
from events.forms import EventForm
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
import reversion


class EventCreateView(PermissionRequiredMixin,
                      SuccessMessageMixin,
                      CreateView):
    permission_required = "events.add_event"
    model = Event
    form_class = EventForm
    template_name = 'events/form.html'
    success_url = reverse_lazy('events:home')
    success_message = "Evento criado com sucesso..."

    def form_valid(self, form):
        with reversion.create_revision():
            reversion.set_user(self.request.user)
            return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Erro no formulário...")
        return super().form_invalid(form)
