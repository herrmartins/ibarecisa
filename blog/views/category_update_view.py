from django.views.generic import UpdateView
from blog.models import Category
from blog.forms import CategoryForm
from django.contrib.auth.mixins import PermissionRequiredMixin


class CategoryUpdateView(PermissionRequiredMixin, UpdateView):
    permission_required = "secretarial.add_meetingminutemodel"
    model = Category
    form_class = CategoryForm
    template_name = "blog/category_form.html"
    context_object_name = "category"
    success_url = "/blog/create/category/"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = Category.objects.all()
        return context
