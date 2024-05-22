from django.views.generic import CreateView
from treasury.models import CategoryModel
from treasury.forms import CategoryModelForm
from django.contrib.auth.mixins import PermissionRequiredMixin


class CategoryCreateView(PermissionRequiredMixin, CreateView):
    permission_required = 'treasury.add_transactionmodel'
    model = CategoryModel
    form_class = CategoryModelForm
    template_name = "treasury/category_form.html"
    success_url = "/treasury/"
