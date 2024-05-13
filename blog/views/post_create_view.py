from django.views.generic.edit import CreateView
from blog.models import Post
from django.urls import reverse_lazy
from blog.forms import PostForm
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin


class PostCreateView(PermissionRequiredMixin, SuccessMessageMixin, CreateView):
    permission_required = "blog.add_post"
    model = Post
    form_class = PostForm
    template_name = 'blog/form.html'
    success_url = reverse_lazy('blog:home')
    success_message = "Post criado com sucesso..."

    def form_invalid(self, form):
        messages.error(self.request, "Erro no formulário...",)
        return super().form_invalid(form)

    def get_form_kwargs(self):
        kwargs = super(PostCreateView, self).get_form_kwargs()
        kwargs['author'] = self.request.user
        return kwargs
