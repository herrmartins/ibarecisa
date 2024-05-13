from django.views.generic import UpdateView
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
