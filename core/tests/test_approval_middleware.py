from django.test import TestCase, RequestFactory, override_settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from core.middleware import ApprovalMiddleware
from users.models import CustomUser


class ApprovalMiddlewareTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def get_response_mock(self, request):
        return "success_response"

    @override_settings(DATABASES={'default': {'NAME': 'production_db'}})
    def test_approved_user_can_access_protected_urls(self):
        """Usuários aprovados devem acessar URLs protegidas normalmente"""
        user = CustomUser.objects.create_user(
            username="approved_user",
            email="approved@example.com",
            password="password123",
            is_approved=True
        )

        middleware = ApprovalMiddleware(self.get_response_mock)
        request = self.factory.get('/secretarial/')
        request.user = user

        response = middleware(request)
        # Usuário aprovado deve passar
        self.assertEqual(response, "success_response")

    @override_settings(DATABASES={'default': {'NAME': 'production_db'}})
    def test_unapproved_user_redirected_to_welcome(self):
        """Usuários não aprovados devem ser redirecionados para welcome"""
        user = CustomUser.objects.create_user(
            username="unapproved_user",
            email="unapproved@example.com",
            password="password123",
            is_approved=False
        )

        middleware = ApprovalMiddleware(self.get_response_mock)
        request = self.factory.get('/secretarial/')
        request.user = user

        response = middleware(request)
        # Deve redirecionar para welcome
        self.assertEqual(response.status_code, 302)
        self.assertIn('/secretarial/welcome', response.url)

    @override_settings(DATABASES={'default': {'NAME': 'production_db'}})
    def test_exempt_urls_not_redirected(self):
        """URLs isentas não devem ser redirecionadas mesmo para usuários não aprovados"""
        user = CustomUser.objects.create_user(
            username="unapproved_user",
            email="unapproved@example.com",
            password="password123",
            is_approved=False
        )

        exempt_urls = [
            '/accounts/login/',
            '/secretarial/welcome',
            '/static/css/style.css',
        ]

        for url in exempt_urls:
            middleware = ApprovalMiddleware(self.get_response_mock)
            request = self.factory.get(url)
            request.user = user

            response = middleware(request)
            # URLs isentas devem passar
            self.assertEqual(response, "success_response")

    @override_settings(DATABASES={'default': {'NAME': 'production_db'}})
    def test_anonymous_user_not_redirected_by_middleware(self):
        """Usuários anônimos não devem ser afetados pelo middleware de aprovação"""
        middleware = ApprovalMiddleware(self.get_response_mock)
        request = self.factory.get('/secretarial/')
        request.user = AnonymousUser()

        response = middleware(request)
        # Deve passar normalmente
        self.assertEqual(response, "success_response")

    def test_middleware_skipped_during_tests(self):
        """Middleware deve ser pulado durante testes (banco com 'memory')"""
        user = CustomUser.objects.create_user(
            username="test_user",
            email="test@example.com",
            password="password123",
            is_approved=False
        )

        middleware = ApprovalMiddleware(self.get_response_mock)
        request = self.factory.get('/secretarial/')
        request.user = user

        # Durante testes (banco com 'memory'), deve pular validação
        response = middleware(request)
        self.assertEqual(response, "success_response")