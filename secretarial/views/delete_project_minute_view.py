from django.contrib.auth.mixins import PermissionRequiredMixin
from django.views.generic.edit import DeleteView
from django.urls import reverse_lazy
from secretarial.models import MinuteProjectModel
from django.shortcuts import redirect


class MinuteProjectDeleteView(PermissionRequiredMixin, DeleteView):
    model = MinuteProjectModel
    permission_required = "secretarial.delete_minuteprojectmodel"
    success_url = reverse_lazy("secretarial:list-minutes-projects")

    def get(self, request, *args, **kwargs):
        return redirect(self.success_url)