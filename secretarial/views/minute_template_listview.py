from django.views.generic import ListView
from secretarial.models import MinuteTemplateModel
from django.contrib.auth.mixins import PermissionRequiredMixin


class MinuteTemplatesListView(PermissionRequiredMixin, ListView):
    permission_required = "secretarial.add_meetingminutemodel"
    model = MinuteTemplateModel
    template_name = "secretarial/list_templates.html"
    context_object_name = "templates"
