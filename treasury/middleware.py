"""
Middleware para garantir que o período contábil do mês atual sempre exista.

O período é criado automaticamente quando alguém acessa o app treasury,
mas o fechamento continua sendo manual (requer assinatura/responsável).
"""

from django.utils import timezone
from django.conf import settings


class AccountingPeriodMiddleware:
    """
    Middleware que cria automaticamente o período contábil do mês atual.

    - Criar período: automático (ao acessar o app)
    - Fechar período: manual (requer responsável)

    Isso garante que sempre haja um período aberto para o mês atual,
    mas mantém o controle do fechamento por uma pessoa autorizada.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Pula o middleware durante testes
        db_name = str(settings.DATABASES['default']['NAME']).lower()
        if 'test' in db_name or 'memory' in db_name:
            return self.get_response(request)

        # Só processa URLs do treasury
        if not request.path.startswith('/treasury/') and not request.path.startswith('/api/treasury/'):
            return self.get_response(request)

        # Só processa se o usuário está autenticado
        if not request.user.is_authenticated:
            return self.get_response(request)

        # Criar período do mês atual se não existir
        self._ensure_current_period_exists()

        return self.get_response(request)

    def _ensure_current_period_exists(self):
        """Garante que o período do mês atual existe."""
        try:
            from treasury.models import AccountingPeriod
            from treasury.services.period_service import PeriodService

            today = timezone.now().date()
            current_month = today.replace(day=1)

            # Verifica se já existe
            if AccountingPeriod.objects.filter(month=current_month).exists():
                return

            # Não existe - criar usando o serviço
            service = PeriodService()
            period = service.get_or_create_period(today)

            # O get_or_create_period já herda o opening_balance do período anterior
            # se ele estiver fechado e tiver closing_balance

        except Exception:
            # Silenciosamente ignora erros para não quebrar o app
            # (pode acontecer durante migrações, etc)
            pass
