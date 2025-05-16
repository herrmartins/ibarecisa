from django.views.generic import TemplateView
from django.contrib.auth.mixins import PermissionRequiredMixin


class NewMinutesEditorView(PermissionRequiredMixin, TemplateView):
    template_name = 'secretarial/new_meeting_minute.html'
    permission_required = "secretarial.add_meetingminutemodel"
