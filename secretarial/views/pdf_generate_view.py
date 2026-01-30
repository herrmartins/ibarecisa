import weasyprint
from django.views.generic import View
from secretarial.models import MeetingMinuteModel
from django.forms.models import model_to_dict
from django.http import HttpResponse
from django.contrib.auth.mixins import PermissionRequiredMixin
from core.core_context_processor import context_user_data
from django.template.loader import render_to_string


class GeneratePDF(PermissionRequiredMixin, View):
    permission_required = "secretarial.view_meetingminutemodel"

    def get(self, request, *args, **kwargs):
        data = MeetingMinuteModel.objects.get(pk=kwargs.get("pk"))

        data_dict = model_to_dict(data)

        # Add formatted names for president and secretary
        if data.president:
            data_dict["president"] = f"{data.president.first_name} {data.president.last_name}"
        if data.secretary:
            data_dict["secretary"] = f"{data.secretary.first_name} {data.secretary.last_name}"

        context_data = context_user_data(request)
        data_dict["church_info"] = context_data.get("church_info")

        # Render HTML template
        html_string = render_to_string("secretarial/minute_pdf.html", data_dict)

        # Get base URL for static files
        base_url = request.build_absolute_uri('/')

        # Generate PDF with WeasyPrint
        weasyprint_html = weasyprint.HTML(string=html_string, base_url=base_url)
        pdf = weasyprint_html.write_pdf()

        if pdf:
            response = HttpResponse(pdf, content_type="application/pdf")
            response[
                "Content-Disposition"
            ] = f'attachment; filename="meeting_minute_{data.pk}.pdf"'
            return response

        return HttpResponse("Failed to generate PDF.", status=500)
