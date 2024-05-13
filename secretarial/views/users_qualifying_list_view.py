from django.views.generic import TemplateView
from users.models import CustomUser
from django.db.models import Q
from django.contrib.auth.mixins import PermissionRequiredMixin


class UsersQualifyingListView(PermissionRequiredMixin, TemplateView):
    permission_required = "users.add_customuser"
    template_name = "secretarial/users_qualifying.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["members"] = CustomUser.objects.filter(
            Q(type=CustomUser.Types.REGULAR) | Q(type=CustomUser.Types.STAFF)
        )
        context["users"] = CustomUser.objects.exclude(
            Q(type=CustomUser.Types.REGULAR) | Q(type=CustomUser.Types.STAFF)
        )

        return context
