from django.views.generic.edit import FormView
from django.contrib.auth.mixins import PermissionRequiredMixin
from blog.forms import CategoryForm
from blog.models import Category


class CategoryFormView(PermissionRequiredMixin, FormView):
    permission_required = "blog.add_post"
    template_name = "blog/category_form.html"
    form_class = CategoryForm
    context_object_name = "category"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = Category.objects.all()
        return context
