from django.test import TestCase, RequestFactory, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.cache import cache
from treasury.views.analysis_view import FinancialAnalysisView
from treasury.models import TransactionModel, CategoryModel, MonthlyBalance
from users.models import CustomUser
from datetime import date
import json


class FinancialAnalysisViewTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = CustomUser.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            cpf='12345678901'
        )
        self.user.is_staff = True
        # Adicionar permissão necessária
        from django.contrib.auth.models import Permission
        permission = Permission.objects.get(codename='view_transactionmodel')
        self.user.user_permissions.add(permission)
        self.user.save()

        # Criar MonthlyBalance inicial (obrigatório para transações)
        self.monthly_balance = MonthlyBalance.objects.create(
            month=date(2024, 1, 1),
            balance=0.00,
            is_first_month=True
        )

        # Criar categorias
        self.category1 = CategoryModel.objects.create(name='Categoria 1')
        self.category2 = CategoryModel.objects.create(name='Categoria 2')

        # Criar transações de teste
        self.transaction1 = TransactionModel.objects.create(
            user=self.user,
            category=self.category1,
            description='Transação 1',
            amount=100.00,
            is_positive=True,
            date=date(2024, 1, 15)
        )
        self.transaction2 = TransactionModel.objects.create(
            user=self.user,
            category=self.category2,
            description='Transação 2',
            amount=-50.00,  # Usar valor negativo para despesa
            is_positive=False,
            date=date(2024, 1, 20)
        )
        # Criar mais uma transação positiva para ter dados mais realistas
        self.transaction3 = TransactionModel.objects.create(
            user=self.user,
            category=self.category1,
            description='Transação 3',
            amount=50.00,
            is_positive=True,
            date=date(2024, 1, 25)
        )

    def test_view_requires_permission(self):
        """Testa se a view requer permissão adequada"""
        client = Client()
        # Usuário sem permissão deve ser redirecionado para login
        response = client.get('/treasury/analysis/')
        self.assertEqual(response.status_code, 302)  # Redirecionamento para login

    def test_view_with_permission(self):
        """Testa se a view funciona com permissão adequada"""
        client = Client()
        client.login(username='testuser', password='testpass123')
        response = client.get('/treasury/analysis/')
        self.assertEqual(response.status_code, 200)

    def test_get_context_data_default_filters(self):
        """Testa o contexto padrão sem filtros"""
        request = self.factory.get('/treasury/analysis/')
        request.user = self.user
        view = FinancialAnalysisView()
        view.request = request

        context = view.get_context_data()

        # Verificar se as chaves básicas estão presentes
        self.assertIn('start_date', context)
        self.assertIn('end_date', context)
        self.assertIn('available_categories', context)
        self.assertIn('total_revenue', context)
        self.assertIn('total_expenses', context)
        self.assertIn('net_balance', context)
        self.assertIn('transaction_count', context)
        self.assertIn('top_categories', context)
        self.assertIn('monthly_data_json', context)
        self.assertIn('category_data_json', context)

    def test_filtered_transactions_by_date(self):
        """Testa filtragem de transações por período"""
        request = self.factory.get('/treasury/analysis/', {
            'start_date': '2024-01-01',
            'end_date': '2024-01-31'
        })
        request.user = self.user
        view = FinancialAnalysisView()
        view.request = request

        transactions = view.get_filtered_transactions(
            date(2024, 1, 1), date(2024, 1, 31)
        )

        self.assertEqual(len(transactions), 3)  # Todas as 3 transações estão em janeiro
        self.assertIn(self.transaction1, transactions)
        self.assertIn(self.transaction2, transactions)
        self.assertIn(self.transaction3, transactions)

    def test_filtered_transactions_by_type(self):
        """Testa filtragem de transações por tipo"""
        request = self.factory.get('/treasury/analysis/', {'type': 'positive'})
        request.user = self.user
        view = FinancialAnalysisView()
        view.request = request

        transactions = view.get_filtered_transactions(
            date(2024, 1, 1), date(2024, 1, 31),
            categories=None, transaction_type='positive'
        )

        self.assertEqual(len(transactions), 2)  # transaction1 e transaction3
        self.assertIn(self.transaction1, transactions)
        self.assertIn(self.transaction3, transactions)
        self.assertNotIn(self.transaction2, transactions)

    def test_filtered_transactions_by_category(self):
        """Testa filtragem de transações por categoria"""
        request = self.factory.get('/treasury/analysis/', {'categories': [self.category1.name]})
        request.user = self.user
        view = FinancialAnalysisView()
        view.request = request

        transactions = view.get_filtered_transactions(
            date(2024, 1, 1), date(2024, 1, 31),
            categories=[self.category1.name]
        )

        self.assertEqual(len(transactions), 2)  # transaction1 e transaction3 têm category1
        self.assertIn(self.transaction1, transactions)
        self.assertIn(self.transaction3, transactions)
        self.assertNotIn(self.transaction2, transactions)

    def test_filtered_transactions_by_amount_range(self):
        """Testa filtragem de transações por faixa de valor"""
        request = self.factory.get('/treasury/analysis/', {
            'min_amount': '40',
            'max_amount': '60'
        })
        request.user = self.user
        view = FinancialAnalysisView()
        view.request = request

        transactions = view.get_filtered_transactions(
            date(2024, 1, 1), date(2024, 1, 31),
            min_amount='40', max_amount='60'
        )

        self.assertEqual(len(transactions), 1)  # apenas transaction3 (50)
        self.assertIn(self.transaction3, transactions)
        self.assertNotIn(self.transaction1, transactions)
        self.assertNotIn(self.transaction2, transactions)  # transaction2 tem amount=-50

    def test_basic_stats_calculation(self):
        """Testa cálculo de estatísticas básicas"""
        transactions = [self.transaction1, self.transaction2, self.transaction3]
        view = FinancialAnalysisView()

        stats = view.get_basic_stats(transactions)

        self.assertEqual(stats['total_revenue'], 150.00)  # abs(100) + abs(50)
        self.assertEqual(stats['total_expenses'], 50.00)  # abs(50)
        self.assertEqual(stats['net_balance'], 100.00)
        self.assertEqual(stats['transaction_count'], 3)
        self.assertAlmostEqual(stats['avg_transaction'], 33.33, places=2)  # (100 + (-50) + 50) / 3

    def test_ai_insights_generation(self):
        """Testa geração de insights de IA"""
        transactions = [self.transaction1, self.transaction2]
        view = FinancialAnalysisView()

        # Limpar cache antes do teste
        cache.clear()

        insights = view.get_ai_insights(transactions, date(2024, 1, 1), date(2024, 1, 31))

        # Deve retornar insights ou mensagem de erro da API
        self.assertIsInstance(insights, str)
        self.assertTrue(len(insights) > 0)

    def test_ai_insights_caching(self):
        """Testa cache de insights de IA"""
        transactions = [self.transaction1, self.transaction2]
        view = FinancialAnalysisView()

        # Limpar cache
        cache.clear()

        # Primeira chamada
        insights1 = view.get_ai_insights(transactions, date(2024, 1, 1), date(2024, 1, 31))

        # Segunda chamada (deve usar cache)
        insights2 = view.get_ai_insights(transactions, date(2024, 1, 1), date(2024, 1, 31))

        # Devem ser iguais (cache funcionou)
        self.assertEqual(insights1, insights2)

    def test_ajax_insights_generation(self):
        """Testa geração de insights via AJAX"""
        request = self.factory.get('/treasury/analysis/', {
            'action': 'generate_insights',
            'start_date': '2024-01-01',
            'end_date': '2024-01-31'
        })
        request.user = self.user
        request.META['HTTP_X_REQUESTED_WITH'] = 'XMLHttpRequest'

        view = FinancialAnalysisView()
        response = view.get(request)

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('insights', data)

    def tearDown(self):
        # Limpar cache após testes
        cache.clear()