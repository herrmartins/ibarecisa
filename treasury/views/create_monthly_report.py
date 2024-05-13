from django.views.generic import CreateView
from treasury.models import MonthlyReportModel
from treasury.forms import GenerateFinanceReportModelForm
from django.contrib.auth.mixins import PermissionRequiredMixin


class MonthlyReportCreateView(PermissionRequiredMixin, CreateView):
    permission_required = [
        "treasury.add_monthlybalance",
        "treasury.add_transactionmodel",
    ]
    model = MonthlyReportModel
    template_name = "treasury/create_monthly_report.html"
    success_url = "/treasury"
    form_class = GenerateFinanceReportModelForm
