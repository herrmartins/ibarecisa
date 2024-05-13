from django.views.generic import TemplateView
from django.contrib.auth.mixins import PermissionRequiredMixin


class MinutesEditorView(PermissionRequiredMixin, TemplateView):
    template_name = 'secretarial/minutes_editor.html'
    permission_required = "secretarial.add_meetingminutemodel"
