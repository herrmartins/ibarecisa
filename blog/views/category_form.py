from django.views.generic.edit import FormView
from django.contrib.auth.mixins import PermissionRequiredMixin
from blog.forms import CategoryForm
from blog.models import Category


class CategoryFormView(PermissionRequiredMixin, FormView):
    permission_required = "blog.add_post"
    template_name = 'blog/category_form.html'
    form_class = CategoryForm

    def get_initial(self):
        category_id = self.kwargs.get('pk')
        category = Category.objects.filter(id=category_id).first()
        initial_data = super().get_initial()
        if category:
            initial_data['title'] = category.title

        return initial_data
