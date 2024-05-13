from django.views.generic.edit import DeleteView
from secretarial.models import MinuteExcerptsModel
from django.urls import reverse
from django.contrib.auth.mixins import PermissionRequiredMixin


class ExcerptDeleteView(PermissionRequiredMixin, DeleteView):
    permission_required = [
        "secretarial.add_meetingminutemodel",
        "secretarial.delete_meetingminutemodel",
    ]
    model = MinuteExcerptsModel
    template_name = "secretarial/excerpt_deleted.html"

    def get_success_url(self):
        return reverse("secretarial:list-excerpts")
