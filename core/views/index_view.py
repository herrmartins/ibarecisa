from django.views.generic import TemplateView
from users.forms import LoginForm
from blog.models import Post


class IndexView(TemplateView):
    template_name = "core/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["login_form"] = LoginForm()
        context["post"] = Post.objects.last()
        return context
