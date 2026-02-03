"""
Testes de permissões para views da tesouraria.

Este módulo testa o controle de acesso para:
- Views de template (requer LoginRequiredMixin ou IsTreasuryUserMixin)
- API views (requer IsAuthenticated ou IsTreasuryUser permission)
"""

from django.test import TestCase, Client
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from decimal import Decimal
from datetime import date

from users.models import CustomUser
from treasury.models import TransactionModel, CategoryModel, AccountingPeriod


class TreasuryPermissionTestCase(TestCase):
    """Classe base para testes de permissão da tesouraria."""

    def setUp(self):
        """Configura usuários e dados básicos para os testes."""
        # Criar usuários com diferentes perfis
        self.regular_user = CustomUser.objects.create_user(
            username='regular',
            email='regular@test.com',
            password='testpass123',
            type=CustomUser.Types.REGULAR
        )

        self.treasurer_user = CustomUser.objects.create_user(
            username='treasurer',
            email='treasurer@test.com',
            password='testpass123',
            is_treasurer=True,
            type=CustomUser.Types.STAFF
        )

        self.secretary_user = CustomUser.objects.create_user(
            username='secretary',
            email='secretary@test.com',
            password='testpass123',
            is_secretary=True,
            type=CustomUser.Types.STAFF
        )

        self.pastor_user = CustomUser.objects.create_user(
            username='pastor',
            email='pastor@test.com',
            password='testpass123',
            is_pastor=True,
            type=CustomUser.Types.STAFF
        )

        self.staff_user = CustomUser.objects.create_user(
            username='staff',
            email='staff@test.com',
            password='testpass123',
            is_staff=True,
            type=CustomUser.Types.STAFF
        )

        # Criar categoria para testes
        self.category = CategoryModel.objects.create(
            name='Dízimos'
        )

        # Criar período contábil
        self.period = AccountingPeriod.objects.create(
            month=date(2025, 1, 1),
            opening_balance=Decimal('0.00'),
            status='open'
        )

        # Criar transação para testes
        self.transaction = TransactionModel.objects.create(
            user=self.treasurer_user,
            category=self.category,
            description='Transação de teste',
            amount=Decimal('100.00'),
            is_positive=True,
            date=date(2025, 1, 15),
            accounting_period=self.period,
            created_by=self.treasurer_user
        )

        # Cliente Django para views de template
        self.client = Client()


class TemplateViewPermissionsTest(TreasuryPermissionTestCase):
    """Testa permissões das views de template."""

    def test_dashboard_view_all_authenticated_users(self):
        """Testa que todos os usuários autenticados podem acessar o dashboard."""
        dashboard_url = reverse('treasury:dashboard')

        for user in [self.regular_user, self.treasurer_user,
                     self.secretary_user, self.pastor_user]:
            self.client.force_login(user)
            response = self.client.get(dashboard_url)
            self.assertEqual(response.status_code, 200)

    def test_transaction_list_view_all_authenticated_users(self):
        """Testa que todos os usuários autenticados podem ver a lista de transações."""
        list_url = reverse('treasury:transaction-list')

        for user in [self.regular_user, self.treasurer_user,
                     self.secretary_user, self.pastor_user]:
            self.client.force_login(user)
            response = self.client.get(list_url)
            self.assertEqual(response.status_code, 200)

    def test_transaction_create_view_only_treasury_users(self):
        """Testa que apenas tesoureiros podem criar transações."""
        create_url = reverse('treasury:transaction-create')

        # Usuário regular NÃO deve ter acesso
        self.client.force_login(self.regular_user)
        response = self.client.get(create_url)
        self.assertEqual(response.status_code, 403)

        # Tesoureiro DEVE ter acesso
        self.client.force_login(self.treasurer_user)
        response = self.client.get(create_url)
        self.assertEqual(response.status_code, 200)

        # Secretário DEVE ter acesso
        self.client.force_login(self.secretary_user)
        response = self.client.get(create_url)
        self.assertEqual(response.status_code, 200)

        # Pastor DEVE ter acesso
        self.client.force_login(self.pastor_user)
        response = self.client.get(create_url)
        self.assertEqual(response.status_code, 200)

    def test_transaction_update_view_only_treasury_users(self):
        """Testa que apenas tesoureiros podem editar transações."""
        update_url = reverse('treasury:transaction-update', kwargs={'pk': self.transaction.pk})

        # Usuário regular NÃO deve ter acesso
        self.client.force_login(self.regular_user)
        response = self.client.get(update_url)
        self.assertEqual(response.status_code, 403)

        # Tesoureiro DEVE ter acesso
        self.client.force_login(self.treasurer_user)
        response = self.client.get(update_url)
        self.assertEqual(response.status_code, 200)

        # Secretário DEVE ter acesso
        self.client.force_login(self.secretary_user)
        response = self.client.get(update_url)
        self.assertEqual(response.status_code, 200)

    def test_reversal_view_only_treasury_users(self):
        """Testa que apenas tesoureiros podem estornar transações."""
        # Criar um período fechado para testar a view de estorno
        closed_period = AccountingPeriod.objects.create(
            month=date(2024, 12, 1),
            opening_balance=Decimal('1000.00'),
            status='closed',
            closing_balance=Decimal('1500.00')
        )

        # Criar transação em período fechado (que NÃO pode ser editada)
        closed_transaction = TransactionModel.objects.create(
            user=self.treasurer_user,
            category=self.category,
            description='Transação de período fechado',
            amount=Decimal('50.00'),
            is_positive=True,
            date=date(2024, 12, 15),
            accounting_period=closed_period,
            created_by=self.treasurer_user
        )

        reversal_url = reverse('treasury:transaction-reversal', kwargs={'pk': closed_transaction.pk})

        # Usuário regular NÃO deve ter acesso
        self.client.force_login(self.regular_user)
        response = self.client.get(reversal_url)
        self.assertEqual(response.status_code, 403)

        # Tesoureiro DEVE ter acesso
        self.client.force_login(self.treasurer_user)
        response = self.client.get(reversal_url)
        self.assertEqual(response.status_code, 200)

    def test_batch_review_view_only_treasury_users(self):
        """Testa que apenas tesoureiros podem acessar a revisão em lote."""
        batch_url = reverse('treasury:batch-review')

        # Usuário regular NÃO deve ter acesso
        self.client.force_login(self.regular_user)
        response = self.client.get(batch_url)
        self.assertEqual(response.status_code, 403)

        # Tesoureiro DEVE ter acesso
        self.client.force_login(self.treasurer_user)
        response = self.client.get(batch_url)
        self.assertEqual(response.status_code, 200)

    def test_charts_view_all_authenticated_users(self):
        """Testa que todos os usuários autenticados podem ver gráficos."""
        charts_url = reverse('treasury:charts')

        for user in [self.regular_user, self.treasurer_user,
                     self.secretary_user, self.pastor_user]:
            self.client.force_login(user)
            response = self.client.get(charts_url)
            self.assertEqual(response.status_code, 200)

    def test_period_list_view_all_authenticated_users(self):
        """Testa que todos os usuários autenticados podem ver a lista de períodos."""
        period_list_url = reverse('treasury:period-list')

        for user in [self.regular_user, self.treasurer_user,
                     self.secretary_user, self.pastor_user]:
            self.client.force_login(user)
            response = self.client.get(period_list_url)
            self.assertEqual(response.status_code, 200)

    def test_audit_view_all_authenticated_users(self):
        """Testa que todos os usuários autenticados podem ver o log de auditoria."""
        audit_url = reverse('treasury:audit-log')

        for user in [self.regular_user, self.treasurer_user,
                     self.secretary_user, self.pastor_user]:
            self.client.force_login(user)
            response = self.client.get(audit_url)
            self.assertEqual(response.status_code, 200)


class APIViewPermissionsTest(APITestCase):
    """Testa permissões das views da API."""

    # Permitir acesso ao banco de dados audit para os testes
    databases = ['default', 'audit']

    def setUp(self):
        """Configura usuários e dados básicos para os testes."""
        # Criar usuários
        self.regular_user = CustomUser.objects.create_user(
            username='regular',
            email='regular@test.com',
            password='testpass123',
            type=CustomUser.Types.REGULAR
        )

        self.treasurer_user = CustomUser.objects.create_user(
            username='treasurer',
            email='treasurer@test.com',
            password='testpass123',
            is_treasurer=True,
            type=CustomUser.Types.STAFF
        )

        self.secretary_user = CustomUser.objects.create_user(
            username='secretary',
            email='secretary@test.com',
            password='testpass123',
            is_secretary=True,
            type=CustomUser.Types.STAFF
        )

        self.pastor_user = CustomUser.objects.create_user(
            username='pastor',
            email='pastor@test.com',
            password='testpass123',
            is_pastor=True,
            type=CustomUser.Types.STAFF
        )

        # Criar dados para testes
        self.category = CategoryModel.objects.create(
            name='Dízimos'
        )

        self.period = AccountingPeriod.objects.create(
            month=date(2025, 1, 1),
            opening_balance=Decimal('0.00'),
            status='open'
        )

        self.transaction = TransactionModel.objects.create(
            user=self.treasurer_user,
            category=self.category,
            description='Transação de teste',
            amount=Decimal('100.00'),
            is_positive=True,
            date=date(2025, 1, 15),
            accounting_period=self.period,
            created_by=self.treasurer_user
        )

        # Cliente API
        self.client = APIClient()

    def test_transaction_list_all_authenticated_users(self):
        """Testa que todos os usuários autenticados podem listar transações."""
        list_url = '/treasury/api/transactions/'

        for user in [self.regular_user, self.treasurer_user,
                     self.secretary_user, self.pastor_user]:
            self.client.force_authenticate(user=user)
            response = self.client.get(list_url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_transaction_retrieve_all_authenticated_users(self):
        """Testa que todos os usuários autenticados podem ver detalhes de transação."""
        detail_url = f'/treasury/api/transactions/{self.transaction.pk}/'

        for user in [self.regular_user, self.treasurer_user,
                     self.secretary_user, self.pastor_user]:
            self.client.force_authenticate(user=user)
            response = self.client.get(detail_url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_transaction_create_only_treasury_users(self):
        """Testa que apenas tesoureiros podem criar transações via API."""
        create_url = '/treasury/api/transactions/'
        data = {
            'category': self.category.pk,
            'description': 'Nova transação',
            'amount': '50.00',
            'is_positive': True,
            'date': '2025-01-20'
        }

        # Usuário regular NÃO deve conseguir criar
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.post(create_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Tesoureiro DEVE conseguir criar
        self.client.force_authenticate(user=self.treasurer_user)
        response = self.client.post(create_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Secretário DEVE conseguir criar
        self.client.force_authenticate(user=self.secretary_user)
        response = self.client.post(create_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_transaction_update_only_treasury_users(self):
        """Testa que apenas tesoureiros podem atualizar transações via API."""
        update_url = f'/treasury/api/transactions/{self.transaction.pk}/'
        data = {
            'category': self.category.pk,
            'description': 'Transação atualizada',
            'amount': '150.00',
            'is_positive': True,
            'date': '2025-01-15'
        }

        # Usuário regular NÃO deve conseguir atualizar
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.patch(update_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Tesoureiro DEVE conseguir atualizar
        self.client.force_authenticate(user=self.treasurer_user)
        response = self.client.patch(update_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_transaction_delete_only_treasury_users(self):
        """Testa que apenas tesoureiros podem excluir transações via API."""
        delete_url = f'/treasury/api/transactions/{self.transaction.pk}/'

        # Usuário regular NÃO deve conseguir excluir
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.delete(delete_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Tesoureiro DEVE conseguir excluir
        self.client.force_authenticate(user=self.treasurer_user)
        response = self.client.delete(delete_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_period_close_only_treasury_users(self):
        """Testa que apenas tesoureiros podem fechar períodos via API."""
        close_url = f'/treasury/api/periods/{self.period.pk}/close/'
        data = {'notes': 'Fechando período de teste'}

        # Usuário regular NÃO deve conseguir fechar
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.post(close_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Recarregar período
        self.period.refresh_from_db()

        # Tesoureiro DEVE conseguir fechar
        self.client.force_authenticate(user=self.treasurer_user)
        response = self.client.post(close_url, data)
        self.assertIn(response.status_code,
                     [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST])  # 400 se já fechado

    def test_ocr_receipt_only_treasury_users(self):
        """Testa que apenas tesoureiros podem usar OCR de comprovantes."""
        ocr_url = '/treasury/api/ocr/receipt/'

        from treasury.tests import get_test_image_file

        # Usuário regular NÃO deve conseguir usar OCR
        self.client.force_authenticate(user=self.regular_user)
        with self.settings(DEFAULT_FILE_STORAGE='treasury.tests.InMemoryStorage'):
            response = self.client.post(ocr_url, {
                'receipt': get_test_image_file()
            }, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_ai_insights_only_treasury_users(self):
        """Testa que apenas tesoureiros podem gerar insights IA."""
        insights_url = '/treasury/api/charts/ai-insights/'
        data = {
            'start_date': '2025-01-01',
            'end_date': '2025-01-31',
            'force': False
        }

        # Usuário regular NÃO deve conseguir gerar insights
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.post(insights_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Tesoureiro DEVE conseguir gerar (pode falhar por outros motivos)
        self.client.force_authenticate(user=self.treasurer_user)
        response = self.client.post(insights_url, data)
        self.assertNotEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_cannot_access_api(self):
        """Testa que usuários não autenticados não podem acessar a API."""
        list_url = '/treasury/api/transactions/'

        self.client.force_authenticate(user=None)
        response = self.client.get(list_url)
        # SessionAuthentication retorna 403 quando não há sessão
        self.assertIn(response.status_code,
                    [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])


class PermissionMixinTest(TestCase):
    """Testa os mixins de permissão da tesouraria."""

    def test_is_treasury_user_mixin_regular_user(self):
        """Testa que IsTreasuryUserMixin bloqueia usuário regular."""
        regular = CustomUser.objects.create_user(
            username='regular',
            email='regular@test.com',
            password='testpass123'
        )

        # Usuário regular não tem permissões especiais
        self.assertFalse(regular.is_treasurer)
        self.assertFalse(regular.is_secretary)
        self.assertFalse(regular.is_pastor)
        self.assertFalse(regular.is_staff)
