from django.contrib.auth.views import PasswordChangeView
from users.forms import ChangeUserPasswordForm
from django.urls import reverse_lazy


class ChangeUserPasswordView(PasswordChangeView):
    template_name = "registration/user_password_change.html"
    form_class = ChangeUserPasswordForm
    success_url = reverse_lazy("core:home")
    sucess_message = "%(user)s, sua senha foi alterada com sucesso..."
