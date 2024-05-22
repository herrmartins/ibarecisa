from django.views.generic import UpdateView
from secretarial.models import MeetingAgendaModel
from secretarial.forms import MinuteAgendaModelForm
from django.contrib.auth.mixins import PermissionRequiredMixin


class CategoryUpdateView(PermissionRequiredMixin, UpdateView):
    permission_required = "secretarial.add_meetingminutemodel"
    model = MeetingAgendaModel
    form_class = MinuteAgendaModelForm
    template_name = "secretarial/agenda_form.html"
    context_object_name = "agenda"
    success_url = "/secretarial/meeting/agenda"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["agenda_titles"] = MeetingAgendaModel.objects.all()
        return context
