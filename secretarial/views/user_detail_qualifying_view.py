from django.views.generic.edit import UpdateView
from users.models import CustomUser
from secretarial.forms import UpdateUserRoleModelForm
from django.contrib.auth.mixins import PermissionRequiredMixin
from secretarial.forms import UserQualifyingForm


class UserDetailQualifyingView(PermissionRequiredMixin, UpdateView):
    permission_required = [
        "users.change_customuser",
        "users.delete_customuser",
        "users.add_customuser",
    ]
    model = CustomUser
    template_name = "secretarial/user_detail_qualify.html"
    form_class = UpdateUserRoleModelForm
    context_object_name = "user_object"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user = CustomUser.objects.get(pk=self.kwargs["pk"])

        context["user_type"] = user.type
        initial_data = {
            "is_pastor": user.is_pastor,
            "is_secretary": user.is_secretary,
            "is_treasurer": user.is_treasurer,
        }
        context["form_q"] = UserQualifyingForm(initial=initial_data)

        return context
