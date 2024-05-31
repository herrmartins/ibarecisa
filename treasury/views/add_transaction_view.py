from django.http import JsonResponse
from django.views import View
from treasury.forms import TransactionForm


class AddTransactionView(View):
    def post(self, request, *args, **kwargs):
        form = TransactionForm(request.POST, request.FILES)
        if form.is_valid():
            transaction = form.save()
            month = transaction.date.month
            year = transaction.date.year
            return JsonResponse({"success": True, "month": month, "year": year})
        else:
            return JsonResponse({"success": False, "errors": form.errors}, status=400)
