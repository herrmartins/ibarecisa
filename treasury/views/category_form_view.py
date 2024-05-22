from django.views.generic import FormView
from treasury.forms import CategoryModelForm
from django.contrib.auth.mixins import PermissionRequiredMixin


class CategoryFormView(PermissionRequiredMixin, FormView):
    permission_required = "treasury.add_transactionmodel"
    template_name = "treasury/category_form.html"
    form_class = CategoryModelForm
    context_object_name = "category"
