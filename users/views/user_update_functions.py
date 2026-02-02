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
        # Store original values before processing
        self.object = self.get_object()
        self.original_is_approved = self.object.is_approved
        self.original_is_pastor = self.object.is_pastor
        self.original_is_secretary = self.object.is_secretary
        self.original_is_treasurer = self.object.is_treasurer
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        # Preservar is_approved se não estiver sendo enviado explicitamente
        if 'is_approved' not in self.request.POST:
            form.instance.is_approved = self.original_is_approved

        # Preservar as outras funções quando apenas uma está sendo alterada
        function_fields = ['is_pastor', 'is_secretary', 'is_treasurer']
        sent_functions = [f for f in function_fields if f in self.request.POST]

        # Se apenas uma função foi enviada (não é uma atualização completa)
        if len(sent_functions) < len(function_fields):
            # Preservar os valores originais das funções não enviadas
            if 'is_pastor' not in self.request.POST:
                form.instance.is_pastor = self.original_is_pastor
            if 'is_secretary' not in self.request.POST:
                form.instance.is_secretary = self.original_is_secretary
            if 'is_treasurer' not in self.request.POST:
                form.instance.is_treasurer = self.original_is_treasurer

        # Regra de negócio: Se tem função, deve ser STAFF ou ONLY_WORKER, nunca REGULAR
        has_any_function = (form.instance.is_pastor or
                           form.instance.is_secretary or
                           form.instance.is_treasurer)

        if has_any_function:
            # Se já é ONLY_WORKER, mantém. Senão, define como STAFF (EQUIPE no Django)
            if form.instance.type != 'ONLY_WORKER' and form.instance.type != 'TRABALHADOR':
                form.instance.type = 'EQUIPE'

        return super().form_valid(form)
