from django.urls import reverse
from django.views.generic import UpdateView
from treasury.models import TransactionModel
from treasury.forms import TransactionForm
from django.contrib.auth.mixins import PermissionRequiredMixin


class TransactionUpdateView(PermissionRequiredMixin, UpdateView):
    permission_required = 'treasury.change_transactionmodel'
    model = TransactionModel
    form_class = TransactionForm
    template_name = "treasury/transaction_updated.html"
    context_object_name = "transaction"
    success_url = "/treasury/"
