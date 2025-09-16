from django.http import JsonResponse
from django.views import View
from django.core.exceptions import ValidationError
from treasury.forms import TransactionForm
import reversion


class AddTransactionView(View):
    def post(self, request, *args, **kwargs):
        form = TransactionForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                with reversion.create_revision():
                    reversion.set_user(request.user)
                    transaction = form.save()
                month = transaction.date.month
                year = transaction.date.year
                return JsonResponse({"success": True, "month": month, "year": year})
            except ValidationError as e:
                return JsonResponse({"success": False, "errors": {"__all__": str(e)}}, status=400)
        else:
            return JsonResponse({"success": False, "errors": form.errors}, status=400)
