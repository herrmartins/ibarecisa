from django.views.generic import TemplateView
from users.forms import RegisterUserForm


class SignupFormView(TemplateView):
    template_name = "users/register.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = RegisterUserForm
        return context
