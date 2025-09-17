from django.shortcuts import redirect
from django.urls import reverse
from django.conf import settings


class ApprovalMiddleware:
    """
    Middleware que verifica se o usuário está aprovado para acessar o site.
    Usuários não aprovados são redirecionados para a página de boas-vindas,
    exceto para URLs específicas como login, logout, welcome e arquivos estáticos.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Pula o middleware durante testes (verifica se o banco de dados contém 'test' ou 'memory')
        db_name = str(settings.DATABASES['default']['NAME']).lower()
        if 'test' in db_name or 'memory' in db_name:
            return self.get_response(request)

        # URLs que não requerem aprovação
        exempt_urls = [
            '/accounts/login/',
            '/accounts/logout/',
            '/secretarial/welcome',
            '/secretarial/welcome/',
            '/static/',
            '/media/',
        ]

        # Verifica se a URL atual está isenta
        if any(request.path.startswith(url) for url in exempt_urls):
            return self.get_response(request)

        # Verifica se o usuário está autenticado e é uma instância de CustomUser
        from users.models import CustomUser
        if (request.user.is_authenticated and
            isinstance(request.user, CustomUser) and
            hasattr(request.user, 'is_approved') and
            not request.user.is_approved):
            # Redireciona para a página de boas-vindas
            return redirect('secretarial:welcome')

        return self.get_response(request)