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
