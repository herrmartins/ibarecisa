from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import JsonResponse
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile as django_contentfile
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
        elif action == 'test_s3':
            return self.test_s3(request)

        return JsonResponse({'error': 'Unknown action'}, status=400)

    def test_email(self, request):
        """Test email sending via Brevo."""
        test_email = 'rafaelmagister@gmail.com'

        try:
            # Log da configuração (removendo senha por segurança)
            logger.info(f"Config Email - HOST: {settings.EMAIL_HOST}, PORT: {settings.EMAIL_PORT}, USER: {settings.EMAIL_HOST_USER}, FROM: {settings.DEFAULT_FROM_EMAIL}")

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
            error_str = str(e)
            logger.error(f"Erro ao enviar email de teste: {error_str}", exc_info=True)

            # Mensagem amigável com dicas
            if '535' in error_str or 'Authentication' in error_str:
                return JsonResponse({
                    'success': False,
                    'error': 'Erro de autenticação no servidor SMTP. Verifique EMAIL_HOST_USER e EMAIL_HOST_PASSWORD no .env'
                }, status=500)
            elif 'timeout' in error_str.lower() or 'timed out' in error_str.lower():
                return JsonResponse({
                    'success': False,
                    'error': 'Timeout ao conectar. Verifique EMAIL_HOST e EMAIL_PORT. Brevo usa porta 587 ou 2525.'
                }, status=500)
            else:
                return JsonResponse({
                    'success': False,
                    'error': f'Erro: {error_str}'
                }, status=500)

    def test_sentry(self, request):
        """Test Sentry error reporting."""
        try:
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

    def test_s3(self, request):
        """Test S3-compatible storage connection."""
        if settings.DEBUG:
            return JsonResponse({
                'success': False,
                'error': 'Ambiente de desenvolvimento usa armazenamento local (não S3).'
            }, status=400)

        try:
            storage = default_storage
            test_content = b'IBARECISA S3 connection test'
            test_path = '_s3_test.txt'

            storage.save(test_path, django_contentfile(test_content))
            exists = storage.exists(test_path)
            if exists:
                storage.delete(test_path)

            bucket = getattr(settings, 'AWS_STORAGE_BUCKET_NAME', 'N/A')
            endpoint = getattr(settings, 'AWS_S3_ENDPOINT_URL', 'N/A')
            logger.info(f"Teste S3 OK - bucket: {bucket}, endpoint: {endpoint}")

            return JsonResponse({
                'success': True,
                'message': f'Conexão S3 OK! Bucket: {bucket} | Endpoint: {endpoint}'
            })
        except Exception as e:
            error_str = str(e)
            logger.error(f"Erro no teste S3: {error_str}", exc_info=True)

            if 'NoCredentialsError' in error_str or 'InvalidAccessKeyId' in error_str:
                hint = 'Verifique AWS_ACCESS_KEY_ID e AWS_SECRET_ACCESS_KEY no .env'
            elif 'NoSuchBucket' in error_str:
                hint = 'O bucket não existe. Verifique AWS_STORAGE_BUCKET_NAME.'
            elif 'ConnectTimeoutError' in error_str or 'timeout' in error_str.lower():
                hint = 'Timeout. Verifique AWS_S3_ENDPOINT_URL e conectividade.'
            else:
                hint = error_str

            return JsonResponse({
                'success': False,
                'error': f'Falha S3: {hint}'
            }, status=500)
