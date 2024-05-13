from django.views.generic.edit import UpdateView
from users.models import CustomUser
from users.forms import UpdateUserProfileModelForm
from django.contrib.auth.mixins import PermissionRequiredMixin
from datetime import datetime
from django.shortcuts import get_object_or_404


class UserProfileUpdateView(PermissionRequiredMixin, UpdateView):
    permission_required = "users.change_customuser"
    model = CustomUser
    form_class = UpdateUserProfileModelForm
    template_name = "users/user_profile_update_form.html"

    def get_permission_required(self):
        if self.get_object() == self.request.user:
            return []
        return super().get_permission_required()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = get_object_or_404(CustomUser, pk=self.kwargs["pk"])
        context["user_id"] = user.id
        return context
