from django.views.generic import DetailView
from secretarial.models import MinuteExcerptsModel
from django.contrib.auth.mixins import PermissionRequiredMixin


class ExcerptDetailView(PermissionRequiredMixin, DetailView):
    permission_required = "secretarial.add_meetingminutemodel"
    model = MinuteExcerptsModel
    template_name = "secretarial/excerpt_detail.html"
    context_object_name = "excerpt"
