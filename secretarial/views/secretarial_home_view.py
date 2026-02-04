from django.views.generic import TemplateView
from users.models import CustomUser
from django.db.models import Q
from secretarial.mixins import IsSecretarialUserMixin


class SecretarialHomeView(IsSecretarialUserMixin, TemplateView):
    template_name = "secretarial/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        number_of_members = CustomUser.objects.filter(
            Q(type=CustomUser.Types.REGULAR) | Q(type=CustomUser.Types.STAFF)
        ).count()
        number_of_visitors = CustomUser.objects.filter(
            type=CustomUser.Types.CONGREGATED
        ).count()

        context["number_of_members"] = number_of_members
        context["number_of_visitors"] = number_of_visitors
        context["total_members"] = number_of_members + number_of_visitors
        return context
