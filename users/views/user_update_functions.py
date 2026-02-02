from django.views.generic import UpdateView
from users.models import CustomUser
from django.contrib.auth.mixins import PermissionRequiredMixin
from secretarial.forms import UserQualifyingForm
from secretarial.forms import UserApprovalForm


class UpdateUserFunctionView(PermissionRequiredMixin, UpdateView):
    permission_required = [
        "users.change_customuser",
        "users.delete_customuser",
        "users.add_customuser",
    ]

    template_name = 'users/update_user_type.html'
    model = CustomUser
    context_object_name = 'user'
    form_class = UserQualifyingForm
    success_url = '/secretarial/users'

    def get_form_class(self):
        if self.request.method == 'POST':
            # Check if only is_approved field is being submitted
            if 'is_approved' in self.request.POST and not any(field in self.request.POST for field in ['is_pastor', 'is_secretary', 'is_treasurer']):
                return UserApprovalForm
        return UserQualifyingForm

    def post(self, request, *args, **kwargs):
        # Store original is_approved value before processing
        self.object = self.get_object()
        self.original_is_approved = self.object.is_approved
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        # Se estamos atualizando apenas funções (não is_approved explicitamente), preservar is_approved original
        # Nota: checkboxes não marcados não são enviados no POST, então precisamos verificar
        # se 'is_approved' está explicitamente presente (não apenas se está no POST como 'false')
        if 'is_approved' not in self.request.POST:
            # Preservar o valor original de is_approved
            form.instance.is_approved = self.original_is_approved
        return super().form_valid(form)
