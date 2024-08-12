from django.views.generic.edit import DeleteView
from treasury.models import MonthlyReportModel
from django.shortcuts import reverse
from django.contrib.auth.mixins import PermissionRequiredMixin


class AnReportDeleteView(PermissionRequiredMixin, DeleteView):
    permission_required = 'treasury.delete_transactionmodel'
    template_name = "treasury/anreport_delete.html"
    model = MonthlyReportModel
    context_object_name = "an_report"

    def get_success_url(self):
        return reverse("treasury:list-financial-reports")
