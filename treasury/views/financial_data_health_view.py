from django.views.generic import TemplateView
from django.contrib.auth.mixins import PermissionRequiredMixin
from treasury import utils


class FinancialDataHealthView(PermissionRequiredMixin, TemplateView):
    permission_required = "treasury.add_transactionmodel"
    template_name = "treasury/financial_healthy.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["integrity"] = utils.check_financial_data_integrity()
        return context
