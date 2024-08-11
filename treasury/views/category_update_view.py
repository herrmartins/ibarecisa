from django.views.generic import UpdateView
from treasury.models import CategoryModel
from treasury.forms import CategoryModelForm
from django.contrib.auth.mixins import PermissionRequiredMixin


class CategoryUpdateView(PermissionRequiredMixin, UpdateView):
    permission_required = "treasury.change_transactionmodel"
    model = CategoryModel
    form_class = CategoryModelForm
    template_name = "treasury/category_form.html"
    context_object_name = "category"
    success_url = "/treasury/"
