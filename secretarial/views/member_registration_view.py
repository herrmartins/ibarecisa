from django.urls import reverse_lazy
from django.views.generic.edit import CreateView
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib import messages
from users.models import CustomUser
from secretarial.forms.member_registration_form import MemberRegistrationForm


class MemberRegistrationView(PermissionRequiredMixin, CreateView):
    model = CustomUser
    form_class = MemberRegistrationForm
    template_name = 'secretarial/member_registration.html'
    success_url = reverse_lazy('secretarial:home')
    permission_required = 'users.add_customuser'

    def form_valid(self, form):
        response = super().form_valid(form)
        user = self.object

        if user.has_usable_password():
            messages.success(
                self.request,
                f"Membro '{user.get_full_name()}' cadastrado com sucesso como usuário ativo."
            )
        else:
            messages.success(
                self.request,
                f"Membro '{user.get_full_name()}' cadastrado com sucesso (sem acesso ao sistema)."
            )

        return response

    def form_invalid(self, form):
        messages.error(
            self.request,
            "Erro ao cadastrar membro. Verifique os dados informados."
        )
        return super().form_invalid(form)