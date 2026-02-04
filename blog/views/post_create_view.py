import logging
from django.views.generic.edit import CreateView
from blog.models import Post
from django.urls import reverse_lazy
from blog.forms import PostForm
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin

logger = logging.getLogger(__name__)


class PostCreateView(PermissionRequiredMixin, SuccessMessageMixin, CreateView):
    permission_required = "blog.add_post"
    model = Post
    form_class = PostForm
    template_name = 'blog/form.html'
    success_url = reverse_lazy('blog:home')
    success_message = "Post criado com sucesso..."

    def form_invalid(self, form):
        logger.error(f"PostCreateView form_invalid - errors: {form.errors}")
        logger.error(f"PostCreateView form_invalid - POST data: {self.request.POST}")
        logger.error(f"PostCreateView form_invalid - cleaned_data: {form.cleaned_data if hasattr(form, 'cleaned_data') else 'N/A'}")
        for field, errors in form.errors.items():
            logger.error(f"PostCreateView form_invalid - field '{field}': {errors}")
        messages.error(self.request, "Erro no formulário...",)
        return super().form_invalid(form)

    def get_form_kwargs(self):
        kwargs = super(PostCreateView, self).get_form_kwargs()
        kwargs['author'] = self.request.user
        logger.info(f"PostCreateView get_form_kwargs - author: {self.request.user}")
        return kwargs

    def post(self, request, *args, **kwargs):
        logger.info(f"PostCreateView post - POST data keys: {list(request.POST.keys())}")
        logger.info(f"PostCreateView post - POST data: {dict(request.POST)}")
        return super().post(request, *args, **kwargs)
