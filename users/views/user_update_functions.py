from django.views.generic import UpdateView
from users.models import CustomUser
from django.contrib.auth.mixins import PermissionRequiredMixin
from secretarial.forms import UserQualifyingForm


class UpdateUserFunctionView(PermissionRequiredMixin, UpdateView):
    permission_required = [
        "users.change_customuser",
        "users.delete_customuser",
        "users.add_customuser",
    ]

    template_name = "users/update_user_type.html"
    model = CustomUser
    context_object_name = "user"
    form_class = UserQualifyingForm
    success_url = "/secretarial/users"
