from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import JsonResponse
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class ConfigView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """Painel de configurações e testes - apenas superusuários."""
    template_name = 'core/config.html'

    def test_func(self):
        """Apenas superusuários podem acessar."""
        return self.request.user.is_superuser

    def post(self, request, *args, **kwargs):
        """Handle test actions."""
        action = request.POST.get('action')

        if action == 'test_email':
            return self.test_email(request)
        elif action == 'test_sentry':
            return self.test_sentry(request)

        return JsonResponse({'error': 'Unknown action'}, status=400)

    def test_email(self, request):
        """Test email sending via Brevo."""
        test_email = 'rafaelmagister@gmail.com'

        try:
            result = send_mail(
                subject='Teste de Email - IBARECISA',
                message='Este é um email de teste do sistema IBARECISA.\n\nSe você recebeu este email, a configuração do Brevo está funcionando corretamente.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[test_email],
                fail_silently=False,
            )
            logger.info(f"Email de teste enviado com sucesso para {test_email}")
            return JsonResponse({
                'success': True,
                'message': f'Email enviado com sucesso para {test_email}'
            })
        except Exception as e:
            logger.error(f"Erro ao enviar email de teste: {e}", exc_info=True)
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)

    def test_sentry(self, request):
        """Test Sentry error reporting."""
        try:
            # Test Sentry by capturing a test exception
            if 'sentry_sdk' in globals():
                import sentry_sdk
                sentry_sdk.capture_message("Teste de Sentry - Painel de Configuração")
                return JsonResponse({
                    'success': True,
                    'message': 'Teste de Sentry enviado com sucesso'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Sentry SDK não está configurado'
                }, status=500)
        except Exception as e:
            logger.error(f"Erro ao enviar teste para Sentry: {e}", exc_info=True)
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
