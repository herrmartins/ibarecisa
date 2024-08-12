from django.views.generic import ListView
from treasury.models import CategoryModel
from django.contrib.auth.mixins import PermissionRequiredMixin


class CategoriesListView(PermissionRequiredMixin, ListView):
    permission_required = 'treasury.view_transactionmodel'
    template_name = "treasury/categories_list.html"
    model = CategoryModel
    context_object_name = "categories"
