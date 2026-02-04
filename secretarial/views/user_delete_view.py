from django.views.generic import DeleteView
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.http import HttpResponseRedirect
from users.models import CustomUser


class UserDeleteView(PermissionRequiredMixin, DeleteView):
    model = CustomUser
    permission_required = "users.delete_customuser"
    success_url = reverse_lazy("secretarial:users-qualifying")

    def get(self, request, *args, **kwargs):
        user = self.get_object()
        # Only allow deletion of SIMPLE_USER, CONGREGATED, and ONLY_WORKER
        if user.type not in [CustomUser.Types.SIMPLE_USER, CustomUser.Types.CONGREGATED, CustomUser.Types.ONLY_WORKER]:
            messages.error(request, "Apenas usuários comuns, congregados e contratados podem ser excluídos.")
            return HttpResponseRedirect(self.success_url)
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        user = self.get_object()
        # Only allow deletion of SIMPLE_USER, CONGREGATED, and ONLY_WORKER
        if user.type not in [CustomUser.Types.SIMPLE_USER, CustomUser.Types.CONGREGATED, CustomUser.Types.ONLY_WORKER]:
            messages.error(request, "Apenas usuários comuns, congregados e contratados podem ser excluídos.")
            return HttpResponseRedirect(self.success_url)
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        user = self.get_object()
        messages.success(self.request, f"Usuário {user.first_name} {user.last_name} excluído com sucesso!")
        return super().form_valid(form)
