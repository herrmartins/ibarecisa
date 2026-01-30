from django.views.generic.edit import DeleteView
from secretarial.models import MinuteExcerptsModel
from django.urls import reverse
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib import messages


class ExcerptDeleteView(PermissionRequiredMixin, DeleteView):
    permission_required = [
        "secretarial.add_meetingminutemodel",
        "secretarial.delete_meetingminutemodel",
    ]
    model = MinuteExcerptsModel
    template_name = "secretarial/update_excerpt.html"

    def get_success_url(self):
        messages.success(self.request, "Trecho deletado com sucesso!")
        return reverse("secretarial:list-excerpts")
