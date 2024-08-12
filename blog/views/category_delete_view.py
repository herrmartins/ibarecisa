from django.views.generic.edit import DeleteView
from blog.models import Category
from django.urls import reverse_lazy
from django.contrib.auth.mixins import PermissionRequiredMixin


class CategoryDeleteView(PermissionRequiredMixin, DeleteView):
    permission_required = "blog.add_post"
    template_name = "blog/category_form.html"
    model = Category
    context_object_name = "category"
    success_url = reverse_lazy('blog:create-post')
