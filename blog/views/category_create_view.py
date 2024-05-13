from django.views.generic.edit import CreateView
from blog.models import Category
from django.urls import reverse_lazy
from blog.forms import CategoryForm
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin


class CategoryCreateView(PermissionRequiredMixin, SuccessMessageMixin, CreateView):
    permission_required = "blog.add_post"
    model = Category
    form_class = CategoryForm
    template_name = 'blog/category_form.html'
    success_url = reverse_lazy('blog:create')
    success_message = "Post criado com sucesso..."

    def form_invalid(self, form):
        messages.error(self.request, "Erro no formulário...",)
        return super().form_invalid(form)