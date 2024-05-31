from django.views import View
from treasury.models import TransactionModel
from django.http import JsonResponse
from django.template.loader import render_to_string


class TransactionListView(View):
    def get(self, request, *args, **kwargs):
        month = request.GET.get("month")
        year = request.GET.get("year")
        transactions = TransactionModel.objects.filter(
            date__year=year, date__month=month
        ).order_by("date")
        balance = 0
        transactions_data = []
        for transaction in transactions:
            balance += transaction.amount
            transactions_data.append(
                {
                    "date": transaction.date.strftime("%d/%m/%Y"),
                    "description": transaction.description,
                    "amount": transaction.amount,
                    "current_balance": balance,
                    "id": transaction.id,
                }
            )
        return JsonResponse({"transactions": transactions_data})
