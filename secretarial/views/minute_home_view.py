from django.views.generic import TemplateView
from secretarial.forms import MinuteProjectModelForm
from secretarial.models import (
    MeetingMinuteModel,
    MinuteProjectModel,
    MinuteExcerptsModel,
    MinuteTemplateModel,
)
from django.contrib.auth.mixins import PermissionRequiredMixin


class MinuteHomeView(PermissionRequiredMixin, TemplateView):
    permission_required = "secretarial.view_meetingminutemodel"
    template_name = "secretarial/minute_home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        minutes = MeetingMinuteModel.objects.all()

        context["form"] = MinuteProjectModelForm()
        context["meeting_minutes"] = MeetingMinuteModel.objects.all().reverse()[:10]
        context["number_of_projects"] = MinuteProjectModel.objects.count()
        context["number_of_excerpts"] = MinuteExcerptsModel.objects.count()
        context["number_of_minutes"] = minutes.count()
        context["minutes"] = minutes
        context["number_of_templates"] = MinuteTemplateModel.objects.count()

        return context
