from django.http import JsonResponse
from django.views import View
from treasury.forms import TransactionForm
from treasury.models import TransactionModel, MonthlyBalance


class AddTransactionView(View):
    def post(self, request, *args, **kwargs):
        form = TransactionForm(request.POST, request.FILES)
        if form.is_valid():
            transaction = form.save()
            month = transaction.date.month
            year = transaction.date.year

            # Use replace before converting to string
            first_day_of_month = transaction.date.replace(day=1)
            monthly_balance = MonthlyBalance.objects.get(month=first_day_of_month)

            # Log the category data
            category = transaction.category

            # Serialize the transaction to JSON
            transaction_data = {
                "id": transaction.id,
                "date": transaction.date.strftime("%Y-%m-%d"),
                "description": transaction.description,
                "category": {
                    "id": category.id,
                    "name": category.name,
                },
                "amount": transaction.amount,
                "current_balance": monthly_balance.balance,
            }

            return JsonResponse(
                {
                    "success": True,
                    "month": month,
                    "year": year,
                    "transaction": transaction_data,
                }
            )
        else:
            return JsonResponse({"success": False, "errors": form.errors}, status=400)
