from django.views.generic import DetailView
from secretarial.models import MeetingMinuteModel
from django.contrib.auth.mixins import PermissionRequiredMixin


class MinuteDetailView(PermissionRequiredMixin, DetailView):
    permission_required = "secretarial.view_meetingminutemodel"
    model = MeetingMinuteModel
    template_name = "secretarial/minute_detail.html"
    context_object_name = "minute"
