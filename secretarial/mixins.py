"""
Mixins de permissão para views da secretaria.
"""

from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied


class IsSecretarialUserMixin(UserPassesTestMixin):
    """
    Mixin que restringe acesso a membros da igreja (staff/REGULAR).

    Usuários autorizados:
    - Membro regular (type == REGULAR)
    - Staff (is_staff)
    - Superuser (is_superuser)

    Congregados e usuários comuns NÃO têm acesso.

    Esta é a mesma lógica usada na navbar para mostrar links de Secretaria/Tesouraria.
    """
    def test_func(self):
        user = self.request.user
        return user.is_authenticated and (user.is_staff or user.type == "REGULAR" or user.is_superuser)

    def handle_no_permission(self):
        """Redireciona para página de permissão negada."""
        if self.request.user.is_authenticated:
            raise PermissionDenied("Apenas membros podem acessar esta página.")
        return super().handle_no_permission()
