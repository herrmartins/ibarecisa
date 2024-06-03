from django.views.generic import TemplateView
from django.contrib.auth.mixins import PermissionRequiredMixin
from treasury import utils

class FinancialDataHealthView(PermissionRequiredMixin, TemplateView):
    permission_required = "treasury.add_transactionmodel"
    template_name = "treasury/financial_healthy.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        integrity_message, monthly_balances_data = utils.check_financial_data_integrity()
        context["integrity"] = integrity_message
        context["monthly_balances"] = monthly_balances_data
        return context
