from django.views.generic import View
from secretarial.models import MeetingMinuteModel
from secretarial.utils import topdfutils
from django.forms.models import model_to_dict
from django.http import HttpResponse
from django.contrib.auth.mixins import PermissionRequiredMixin
from core.core_context_processor import context_user_data


class GeneratePDF(PermissionRequiredMixin, View):
    permission_required = "secretarial.view_meetingminutemodel"

    def get(self, request, *args, **kwargs):
        data = MeetingMinuteModel.objects.get(pk=kwargs.get("pk"))

        data_dict = model_to_dict(data)

        context_data = context_user_data(request)
        data_dict["church_info"] = context_data.get("church_info")

        pdf = topdfutils.render_to_pdf("secretarial/minute_pdf.html", data_dict)

        if pdf:
            response = HttpResponse(pdf, content_type="application/pdf")
            response[
                "Content-Disposition"
            ] = f'attachment; filename="meeting_minute_{data.pk}.pdf"'
            return response

        return HttpResponse("Failed to generate PDF.", status=500)
