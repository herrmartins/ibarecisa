from django.views.generic import ListView
from treasury.models import MonthlyBalance, MonthlyReportModel
from django.contrib.auth.mixins import PermissionRequiredMixin


class FinanceReportsListView(PermissionRequiredMixin, ListView):
    permission_required = "treasury.view_transactionmodel"
    template_name = "treasury/reports_list.html"
    model = MonthlyBalance
    context_object_name = "reports"

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(object_list=object_list, **kwargs)
        context["analytical_reports"] = MonthlyReportModel.objects.all()
        return context
