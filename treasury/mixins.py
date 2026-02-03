"""
Mixins de permissão para views da tesouraria.
"""

from django.contrib.auth.mixins import AccessMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied


class IsTreasuryUserMixin(UserPassesTestMixin):
    """
    Mixin que restringe acesso a usuários da tesouraria/secretaria/pastoral.

    Usuários autorizados:
    - Tesoureiro (is_treasurer)
    - Secretário (is_secretary)
    - Pastor (is_pastor)
    - Staff (is_staff)
    - Superuser (is_superuser)
    """
    def test_func(self):
        return (
            self.request.user.is_authenticated and (
                self.request.user.is_treasurer or
                self.request.user.is_secretary or
                self.request.user.is_pastor or
                self.request.user.is_staff or
                self.request.user.is_superuser
            )
        )

    def handle_no_permission(self):
        """Redireciona para página de permissão negada."""
        if self.request.user.is_authenticated:
            raise PermissionDenied("Você não tem permissão para acessar esta página.")
        return super().handle_no_permission()


class IsAdminOrTreasuryUserMixin(UserPassesTestMixin):
    """
    Mixin que restringe acesso a administradores.

    Usuários autorizados:
    - Pastor (is_pastor)
    - Staff (is_staff)
    - Superuser (is_superuser)
    """
    def test_func(self):
        return (
            self.request.user.is_authenticated and (
                self.request.user.is_staff or
                self.request.user.is_superuser or
                self.request.user.is_pastor
            )
        )

    def handle_no_permission(self):
        """Redireciona para página de permissão negada."""
        if self.request.user.is_authenticated:
            raise PermissionDenied("Você não tem permissão para acessar esta página.")
        return super().handle_no_permission()
