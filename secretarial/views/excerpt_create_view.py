from django.views.generic import CreateView
from secretarial.models import MinuteExcerptsModel
from django.contrib.auth.mixins import PermissionRequiredMixin


class ExcerptCreateView(PermissionRequiredMixin, CreateView):
    permission_required = "secretarial.add_meetingminutemodel"
    model = MinuteExcerptsModel
    template_name = "secretarial/excerpt_created.html"
    fields = ["title", "excerpt"]
