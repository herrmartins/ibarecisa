from django.views.generic import TemplateView
from django.contrib.auth.mixins import PermissionRequiredMixin


class ConfigView(PermissionRequiredMixin, TemplateView):
    permission_required = [
        "users.add_customuser",
    ]
    template_name = 'core/config.html'
