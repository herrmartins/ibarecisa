from django.views.generic import ListView
from secretarial.models import MeetingMinuteModel
from django.contrib.auth.mixins import PermissionRequiredMixin


class MinutesListView(PermissionRequiredMixin, ListView):
    permission_required = "secretarial.view_meetingminutemodel"
    model = MeetingMinuteModel
    template_name = 'secretarial/list_minutes.html'
    context_object_name = 'minutes'
    ordering = "-meeting_date"
