from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.messages.middleware import MessageMiddleware
from django.urls import reverse
from django.http import HttpResponse
from unittest.mock import patch, MagicMock

from secretarial.views.send_password_email_view import SendPasswordEmailView

CustomUser = get_user_model()


class SendPasswordEmailViewTest(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.view = SendPasswordEmailView()

        self.secretary_user = CustomUser.objects.create_user(
            username='secretary',
            email='secretary@test.com',
            password='password123',
            first_name='João',
            last_name='Secretário',
            is_secretary=True
        )

        secretary_group, _ = Group.objects.get_or_create(name='secretary')
        self.secretary_user.groups.add(secretary_group)
        self.secretary_user.save()

        self.member_without_password = CustomUser.objects.create(
            username='member_no_pass',
            email='member@test.com',
            first_name='Maria',
            last_name='Membro',
            type=CustomUser.Types.REGULAR
        )
        self.member_without_password.set_unusable_password()
        self.member_without_password.save()

        self.member_with_password = CustomUser.objects.create_user(
            username='member_with_pass',
            email='member2@test.com',
            password='password123',
            first_name='José',
            last_name='Membro',
            type=CustomUser.Types.REGULAR
        )

        self.member_without_email = CustomUser.objects.create(
            username='member_no_email',
            first_name='Ana',
            last_name='Membro',
            type=CustomUser.Types.REGULAR
        )

    def _setup_request(self, request):
        def get_response(request):
            return HttpResponse()
        middleware = SessionMiddleware(get_response)
        middleware.process_request(request)
        request.session.save()

        middleware = MessageMiddleware(get_response)
        middleware.process_request(request)

        messages = FallbackStorage(request)
        request._messages = messages

        request.user = self.secretary_user
        return request

    @patch('secretarial.views.send_password_email_view.send_message')
    def test_send_password_email_success(self, mock_send_message):
        self.assertFalse(self.member_without_password.has_usable_password())

        request = self.factory.post(reverse('secretarial:send-password-email', kwargs={'pk': self.member_without_password.pk}))
        request = self._setup_request(request)

        response = self.view.post(request, pk=self.member_without_password.pk)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('secretarial:users-qualifying'))

        mock_send_message.assert_called_once()
        args, kwargs = mock_send_message.call_args
        self.assertEqual(args[0], "Bem-vindo à IBARECISA - Defina sua senha")
        self.assertIn("definir sua senha", args[1])
        self.assertEqual(args[2], [self.member_without_password.email])

        messages = list(request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn("enviado com sucesso", str(messages[0]))

    def test_send_password_email_user_with_password(self):
        request = self.factory.post(reverse('secretarial:send-password-email', kwargs={'pk': self.member_with_password.pk}))
        request = self._setup_request(request)

        response = self.view.post(request, pk=self.member_with_password.pk)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('secretarial:users-qualifying'))

        messages = list(request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn("já possui senha", str(messages[0]))

    def test_send_password_email_user_without_email(self):
        request = self.factory.post(reverse('secretarial:send-password-email', kwargs={'pk': self.member_without_email.pk}))
        request = self._setup_request(request)

        response = self.view.post(request, pk=self.member_without_email.pk)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('secretarial:users-qualifying'))

        messages = list(request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn("e-mail não cadastrado", str(messages[0]))

    def test_send_password_email_nonexistent_user(self):
        request = self.factory.post(reverse('secretarial:send-password-email', kwargs={'pk': 9999}))
        request = self._setup_request(request)

        with self.assertRaises(Exception):  # Deve lançar DoesNotExist
            self.view.post(request, pk=9999)

    @patch('secretarial.views.send_password_email_view.send_message')
    def test_send_password_email_send_message_failure(self, mock_send_message):
        mock_send_message.side_effect = Exception("Erro de envio")

        request = self.factory.post(reverse('secretarial:send-password-email', kwargs={'pk': self.member_without_password.pk}))
        request = self._setup_request(request)

        response = self.view.post(request, pk=self.member_without_password.pk)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('secretarial:users-qualifying'))

        messages = list(request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn("Erro ao enviar e-mail", str(messages[0]))

    def test_permission_required(self):
        regular_user = CustomUser.objects.create_user(
            username='regular',
            email='regular@test.com',
            password='password123'
        )

        request = self.factory.post(reverse('secretarial:send-password-email', kwargs={'pk': self.member_without_password.pk}))
        request = self._setup_request(request)
        request.user = regular_user

        self.view.request = request

        from django.core.exceptions import PermissionDenied
        with self.assertRaises(PermissionDenied):
            self.view.dispatch(request, pk=self.member_without_password.pk)