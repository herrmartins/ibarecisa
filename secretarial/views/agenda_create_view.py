from django.views.generic import CreateView
from secretarial.models import MeetingAgendaModel
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.urls import reverse_lazy


class AgendaCreateView(PermissionRequiredMixin, CreateView):
    permission_required = "secretarial.add_meetingminutemodel"
    model = MeetingAgendaModel
    template_name = 'secretarial/agenda_form.html'
    fields = ['agenda_title',]
    success_url = reverse_lazy("secretarial:agenda-form")
