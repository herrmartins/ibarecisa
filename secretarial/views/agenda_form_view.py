from django.views.generic import FormView
from secretarial.forms import MinuteAgendaModelForm
from django.contrib.auth.mixins import PermissionRequiredMixin
from secretarial.models import MeetingAgendaModel


class AgendaFormView(PermissionRequiredMixin, FormView):
    permission_required = "secretarial.add_meetingminutemodel"
    template_name = 'secretarial/agenda_form.html'
    form_class = MinuteAgendaModelForm
    success_url = 'secretarial/meeting/agenda/'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["agenda_titles"] = MeetingAgendaModel.objects.all()
        return context
