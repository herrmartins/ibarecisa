from django.views.generic import UpdateView
from django.urls import reverse_lazy
from django.contrib import messages
from secretarial.models import MinuteProjectModel
from secretarial.forms import MinuteProjectEditForm
from django.contrib.auth.mixins import PermissionRequiredMixin
import reversion


class MinuteProjectEditView(PermissionRequiredMixin, UpdateView):
    permission_required = "secretarial.change_minuteprojectmodel"
    model = MinuteProjectModel
    form_class = MinuteProjectEditForm
    template_name = 'secretarial/minute_project_edit.html'
    success_url = reverse_lazy('secretarial:list-minutes-projects')

    def form_valid(self, form):
        with reversion.create_revision():
            reversion.set_user(self.request.user)
            messages.success(self.request, 'Projeto de ata atualizado com sucesso!')
            return super().form_valid(form)