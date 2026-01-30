from django.views.generic.edit import DeleteView
from secretarial.models import MinuteTemplateModel
from django.urls import reverse
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib import messages


class TemplateDeleteView(PermissionRequiredMixin, DeleteView):
    permission_required = [
        "secretarial.add_meetingminutemodel",
        "secretarial.delete_meetingminutemodel",
    ]
    model = MinuteTemplateModel
    template_name = "secretarial/list_templates.html"

    def get_success_url(self):
        messages.success(self.request, "Modelo de ata deletado com sucesso!")
        return reverse("secretarial:list-templates")
