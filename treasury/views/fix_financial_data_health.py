from django.views.generic import View
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages
from treasury.models import MonthlyBalance, TransactionModel
from django.db.models import Sum


class FixFinancialDataView(PermissionRequiredMixin, View):
    permission_required = "treasury.add_transactionmodel"

    def post(self, request, *args, **kwargs):
        try:
            # Fetch the first month balance
            first_month_balance = MonthlyBalance.objects.get(is_first_month=True)
            current_balance = first_month_balance.balance

            # Fetch and update subsequent balances
            for balance in MonthlyBalance.objects.order_by("month").exclude(
                is_first_month=True
            ):
                aggregate_transactions = (
                    TransactionModel.objects.filter(
                        date__month=balance.month.month, date__year=balance.month.year
                    ).aggregate(total=Sum("amount"))["total"]
                    or 0
                )
                current_balance += aggregate_transactions
                balance.balance = current_balance
                balance.save()

            messages.success(request, "Financial data has been successfully corrected.")
        except Exception as e:
            messages.error(
                request, f"An error occurred while fixing financial data: {e}"
            )

        return redirect(reverse("treasury:check-treasury-health"))
