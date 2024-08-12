from django.views.generic import ListView
from secretarial.models import MinuteProjectModel
from django.contrib.auth.mixins import PermissionRequiredMixin


class MinutesProjectListView(PermissionRequiredMixin, ListView):
    permission_required = "secretarial.add_meetingminutemodel"
    model = MinuteProjectModel
    template_name = 'secretarial/list_minutes_projects.html'
    ordering = ['-created']
    context_object_name = 'minutes'
