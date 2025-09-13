from django.views.generic import DetailView
from django.urls import reverse
from secretarial.models import MeetingMinuteModel
from django.contrib.auth.mixins import PermissionRequiredMixin
from secretarial.forms import MinuteFileModelForm


class MinuteDetailView(PermissionRequiredMixin, DetailView):
    permission_required = "secretarial.view_meetingminutemodel"
    model = MeetingMinuteModel
    template_name = 'secretarial/minute_detail.html'
    context_object_name = 'minute'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        minute = context.get('minute')
        context['attachments'] = minute.attachments.all() if minute else []
        context['file_form'] = MinuteFileModelForm()
        context['file_upload_url'] = reverse('secretarial:minute-attachment-add', kwargs={'minute_pk': minute.pk}) if minute else ''
        return context
