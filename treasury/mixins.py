"""
Mixins de permissão para views da tesouraria.
"""

from django.contrib.auth.mixins import AccessMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied


class IsTreasurerOnlyMixin(UserPassesTestMixin):
    """
    Mixin que restringe acesso APENAS a tesoureiros.

    Usuários autorizados:
    - Tesoureiro (is_treasurer)
    - Superuser (is_superuser)

    Secretários, pastores e staff em geral NÃO têm acesso.
    """
    def test_func(self):
        user = self.request.user
        if not user.is_authenticated:
            return False

        # Superuser pode tudo
        if user.is_superuser:
            return True

        # Apenas tesoureiros (não secretários/pastores)
        return user.is_treasurer

    def handle_no_permission(self):
        """Redireciona para página de permissão negada."""
        if self.request.user.is_authenticated:
            raise PermissionDenied("Apenas tesoureiros podem acessar esta página.")
        return super().handle_no_permission()


class IsTreasuryUserMixin(UserPassesTestMixin):
    """
    Mixin que restringe acesso a membros da igreja (visualização).

    Usuários autorizados:
    - Membro regular (type == REGULAR)
    - Tesoureiro (is_treasurer)
    - Secretário (is_secretary)
    - Pastor (is_pastor)
    - Staff (is_staff)
    - Superuser (is_superuser)

    Congregados e usuários simples NÃO têm acesso.
    """
    def test_func(self):
        user = self.request.user
        if not user.is_authenticated:
            return False

        # Membros regulares podem visualizar
        if user.type == "REGULAR":
            return True

        # Staff e funções especiais
        return (
            user.is_treasurer or
            user.is_secretary or
            user.is_pastor or
            user.is_staff or
            user.is_superuser
        )

    def handle_no_permission(self):
        """Redireciona para página de permissão negada."""
        if self.request.user.is_authenticated:
            raise PermissionDenied("Você não tem permissão para acessar esta página.")
        return super().handle_no_permission()


class IsAdminOrTreasuryUserMixin(UserPassesTestMixin):
    """
    Mixin que restringe acesso a administradores da tesouraria.

    Usuários autorizados:
    - Tesoureiro (is_treasurer)
    - Secretário (is_secretary)
    - Pastor (is_pastor)
    - Staff (is_staff)
    - Superuser (is_superuser)
    """
    def test_func(self):
        user = self.request.user
        return (
            user.is_authenticated and (
                user.is_staff or
                user.is_superuser or
                user.is_treasurer or
                user.is_secretary or
                user.is_pastor
            )
        )

    def handle_no_permission(self):
        """Redireciona para página de permissão negada."""
        if self.request.user.is_authenticated:
            raise PermissionDenied("Você não tem permissão para acessar esta página.")
        return super().handle_no_permission()


class IsSuperUserOnlyMixin(UserPassesTestMixin):
    """
    Mixin que restringe acesso APENAS a superusuários.

    Usuários autorizados:
    - Superuser (is_superuser) apenas

    Tesoureiros, secretários, pastores e staff em geral NÃO têm acesso.
    """
    def test_func(self):
        user = self.request.user
        return user.is_authenticated and user.is_superuser

    def handle_no_permission(self):
        """Redireciona para página de permissão negada."""
        if self.request.user.is_authenticated:
            raise PermissionDenied("Apenas superusuários podem acessar esta página.")
        return super().handle_no_permission()
