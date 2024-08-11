from django.views.generic import ListView
from secretarial.models import MinuteExcerptsModel
from django.contrib.auth.mixins import PermissionRequiredMixin


class MinutesExcerptsListView(PermissionRequiredMixin, ListView):
    permission_required = "secretarial.add_meetingminutemodel"
    model = MinuteExcerptsModel
    template_name = "secretarial/list_excerpts.html"
    context_object_name = "excerpts"
