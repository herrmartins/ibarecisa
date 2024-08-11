from django.views.generic import CreateView
from secretarial.forms import MinuteModelForm
from secretarial.models import (
    MinuteProjectModel,
    MeetingMinuteModel,
    MinuteExcerptsModel,
)
from django.contrib.auth.mixins import PermissionRequiredMixin


class MinuteCreateView(PermissionRequiredMixin, CreateView):
    permission_required = "secretarial.add_meetingminutemodel"
    form_class = MinuteModelForm
    template_name = "secretarial/minute_created.html"
    context_object_name = "minute"
    model = MeetingMinuteModel

    # Tirei, parece inútil, não tem url pattern para pegar PK... Vou ter um tempo..
    """ def get_initial(self):
        initial = super().get_initial()

        if self.kwargs.get("pk"):
            minute_data = MinuteProjectModel.objects.get(
                pk=self.kwargs.get("pk"))
            print(minute_data)
            initial["president"] = minute_data.president
            initial["secretary"] = minute_data.secretary
            initial["meeting_date"] = minute_data.meeting_date.isoformat()
            initial["number_of_attendees"] = minute_data.number_of_atendees
            initial["body"] = minute_data.body
            initial["agenda"] = minute_data.meeting_agenda.all()
        return initial """

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["excerpts_list"] = MinuteExcerptsModel.objects.all().order_by(
            "-times_used"
        )

        return context
