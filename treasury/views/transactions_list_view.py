from django.http import JsonResponse
from django.views import View
from treasury.models import TransactionModel
from treasury.utils import (
    get_month_balance,
    get_previous_month,
    get_aggregate_transactions,
)
from datetime import date


class TransactionListView(View):
    def get(self, request, *args, **kwargs):
        month = int(request.GET.get("month"))
        year = int(request.GET.get("year"))

        transactions = TransactionModel.objects.filter(
            date__year=year, date__month=month
        ).order_by("date")

        post_transaction_balance = 0
        transactions_data = []
        for transaction in transactions:
            post_transaction_balance += transaction.amount
            transactions_data.append(
                {
                    "date": transaction.date.strftime("%Y-%m-%d"),
                    "description": transaction.description,
                    "amount": transaction.amount,
                    "current_balance": post_transaction_balance,
                    "id": transaction.id,
                }
            )

        positive_transactions = get_aggregate_transactions(year, month, True)
        negative_transactions = get_aggregate_transactions(year, month, False)

        monthly_result = get_aggregate_transactions(year, month)

        current_date = date(year, month, 1)

        previous_month_balance = get_month_balance(get_previous_month(current_date))
        current_monthly_balance = previous_month_balance + monthly_result

        return JsonResponse(
            {
                "transactions": transactions_data,
                "current_balance": current_monthly_balance,
                "monthly_result": monthly_result,
                "positive_transactions": positive_transactions,
                "negative_transactions": negative_transactions,
                "previous_month_balance": previous_month_balance,
            }
        )
