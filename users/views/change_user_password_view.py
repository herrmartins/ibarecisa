from django.contrib.auth.views import PasswordChangeView
from users.forms import ChangeUserPasswordForm
from django.urls import reverse_lazy


class ChangeUserPasswordView(PasswordChangeView):
    template_name = "registration/user_password_change.html"
    form_class = ChangeUserPasswordForm

    def get_success_url(self):
        return reverse_lazy('users:user-profile', kwargs={'pk': self.request.user.pk})
