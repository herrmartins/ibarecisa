from django.views.generic import UpdateView
from django.http import JsonResponse
from users.models import CustomUser
from django.contrib.auth.mixins import PermissionRequiredMixin
from secretarial.forms import UpdateUserRoleModelForm


class UpdateUserTypeView(PermissionRequiredMixin, UpdateView):
    permission_required = "users.change_customuser"

    template_name = "users/update_user_type.html"
    model = CustomUser
    context_object_name = "user"
    form_class = UpdateUserRoleModelForm
    success_url = "/secretarial/users"

    def form_valid(self, form):
        # Se o tipo está sendo definido como REGULAR ou STAFF, aprovar automaticamente
        if form.instance.type in ['REGULAR', 'STAFF']:
            form.instance.is_approved = True

        # Se o tipo está sendo definido como REGULAR, desmarcar todas as funções
        if form.instance.type == 'REGULAR':
            form.instance.is_pastor = False
            form.instance.is_secretary = False
            form.instance.is_treasurer = False

        # Salvar o objeto
        self.object = form.save()

        # Se AJAX request, retornar JSON
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})

        # Se não é AJAX, redirecionar
        from django.http import HttpResponseRedirect
        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form):
        # Se AJAX request, retornar erros como JSON
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)
        return super().form_invalid(form)
