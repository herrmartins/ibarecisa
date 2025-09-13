from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import CreateView
from django.contrib.auth.mixins import PermissionRequiredMixin

from secretarial.models import MeetingMinuteModel, MinuteFileModel
from secretarial.forms import MinuteFileModelForm


class MinuteFileUploadView(PermissionRequiredMixin, CreateView):
    permission_required = "secretarial.add_minutefilemodel"
    model = MinuteFileModel
    form_class = MinuteFileModelForm
    template_name = "secretarial/minute_file_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.minute = get_object_or_404(MeetingMinuteModel, pk=kwargs.get("minute_pk"))
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.minute = self.minute
        obj.save()
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse("secretarial:minute-detail-view", kwargs={"pk": self.minute.pk})
