from django.views.generic import View
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages
from treasury.models import MonthlyBalance, TransactionModel
from django.db.models import Sum
import logging

logger = logging.getLogger(__name__)

class FixFinancialDataView(PermissionRequiredMixin, View):
    permission_required = "treasury.add_transactionmodel"

    def has_permission(self):
        """
        Allow superusers and users with the required permission.
        """
        if self.request.method == "GET" and self.request.user.is_superuser:
            return True
        return super().has_permission()

    def get(self, request, *args, **kwargs):
        """
        Handle GET requests to fix financial data.
        """
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
        except MonthlyBalance.DoesNotExist:
            messages.error(request, "First month balance is missing.")
        except Exception as e:
            logger.error(f"Error fixing financial data: {e}")
            messages.error(
                request, f"An error occurred while fixing financial data: {e}"
            )

        return redirect(reverse("treasury:check-treasury-health"))
