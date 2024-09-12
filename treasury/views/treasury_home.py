from django.views.generic import TemplateView
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from django.shortcuts import reverse
from django.http import HttpResponseRedirect
from treasury.forms import TransactionForm, InitialBalanceForm
from treasury.models import MonthlyBalance
from django.contrib.auth.mixins import PermissionRequiredMixin
from treasury.utils import check_and_create_missing_balances, get_monthly_balances_list
from django.db.models.functions import TruncYear


class TreasuryHomeView(PermissionRequiredMixin, TemplateView):
    permission_required = "treasury.view_transactionmodel"
    template_name = "treasury/home.html"

    def get(self, request, *args, **kwargs):
        current_date = timezone.now()
        previous_month = current_date - relativedelta(months=1)
        first_month = MonthlyBalance.objects.filter(is_first_month=True)
        if first_month:
            if not MonthlyBalance.objects.filter(
                month__year=previous_month.year, month__month=previous_month.month
            ).exists():
                check_and_create_missing_balances(current_date)
                return HttpResponseRedirect(reverse("treasury:home"))

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        monthly_balances = MonthlyBalance.objects.all().order_by("month")

        year_month_map = {}
        first_month_balance = monthly_balances.filter(is_first_month=True).first()

        for balance in monthly_balances:
            year = balance.month.year
            month = balance.month.month

            if first_month_balance and balance == first_month_balance:
                continue  # Skip the first month as it's a reference month

            if year not in year_month_map:
                year_month_map[year] = []

            year_month_map[year].append(month)

        context["year_month_map"] = year_month_map
        context["year_list"] = sorted(year_month_map.keys())

        current_date = timezone.now()
        previous_month = current_date - relativedelta(months=1)
        try:
            previous_month_balance = MonthlyBalance.objects.get(
                month__year=previous_month.year,
                month__month=previous_month.month,
            )
            context[
                "previous_month_account_balance"
            ] = f"R$ {previous_month_balance.balance}"
        except MonthlyBalance.DoesNotExist:
            print("Não há registro do mês passado...")

        form = TransactionForm(user=self.request.user)
        context["form_transaction"] = form
        context["month"] = current_date.month
        context["year"] = current_date.year

        if MonthlyBalance.objects.count() == 0:
            context["form_balance"] = InitialBalanceForm

        return context
