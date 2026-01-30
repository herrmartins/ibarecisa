from django.views.generic import CreateView
from secretarial.models import MinuteExcerptsModel
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.urls import reverse
from django.contrib import messages


class ExcerptCreateView(PermissionRequiredMixin, CreateView):
    permission_required = "secretarial.add_meetingminutemodel"
    model = MinuteExcerptsModel
    template_name = 'secretarial/update_excerpt.html'
    fields = ['title', 'excerpt']

    def get_success_url(self):
        messages.success(self.request, "Trecho criado com sucesso!")
        return reverse("secretarial:list-excerpts")
