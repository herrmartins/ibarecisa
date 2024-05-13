from django.views.generic import CreateView
from treasury.models import MonthlyBalance
from treasury.forms import InitialBalanceForm
from django.contrib.auth.mixins import PermissionRequiredMixin


class InitialBalanceCreateView(PermissionRequiredMixin, CreateView):
    permission_required = 'treasury.add_transactionmodel'
    model = MonthlyBalance
    form_class = InitialBalanceForm
    template_name = "treasury/monthly_balance_created.html"
    success_url = "/treasury/"
