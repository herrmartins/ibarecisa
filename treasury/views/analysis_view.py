from django.views.generic import TemplateView
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db.models import Sum, Q, Count
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from treasury.models import TransactionModel, CategoryModel, MonthlyBalance
from django.http import JsonResponse
from django.core.cache import cache
from secretarial.utils.ai_utils import get_mistral_model_for_task
import json
import requests
from django.conf import settings
import hashlib


class FinancialAnalysisView(PermissionRequiredMixin, TemplateView):
    permission_required = "treasury.view_transactionmodel"
    template_name = "treasury/financial_analysis.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Filtros de período
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')

        if not start_date or not end_date:
            # Padrão: últimos 12 meses
            end_date = timezone.now().date()
            start_date = end_date - relativedelta(months=12)

        context['start_date'] = start_date
        context['end_date'] = end_date

        # Filtros adicionais
        selected_categories = self.request.GET.getlist('categories')
        transaction_type = self.request.GET.get('type')  # 'positive', 'negative', or None for both
        min_amount = self.request.GET.get('min_amount')
        max_amount = self.request.GET.get('max_amount')

        context.update({
            'selected_categories': selected_categories,
            'transaction_type': transaction_type,
            'min_amount': min_amount,
            'max_amount': max_amount,
        })

        # Obter transações filtradas
        transactions = self.get_filtered_transactions(
            start_date, end_date, selected_categories,
            transaction_type, min_amount, max_amount
        )

        # Estatísticas básicas
        context.update(self.get_basic_stats(transactions))

        # Dados para gráficos
        context.update(self.get_chart_data(transactions, start_date, end_date))

        # Lista de todas as categorias disponíveis
        context['available_categories'] = self.get_available_categories()

        # Insights de AI (persistentes)
        context['ai_insights'] = self.get_ai_insights(transactions, start_date, end_date)

        return context

    def get_filtered_transactions(self, start_date, end_date, categories=None,
                                transaction_type=None, min_amount=None, max_amount=None):
        """Retorna transações filtradas pelos critérios especificados"""
        filters = {
            'date__gte': start_date,
            'date__lte': end_date,
        }

        if categories:
            filters['category__name__in'] = categories

        if transaction_type == 'positive':
            filters['is_positive'] = True
        elif transaction_type == 'negative':
            filters['is_positive'] = False

        if min_amount:
            # Como usamos abs() nos cálculos, filtramos considerando valores absolutos
            filters['amount__gte'] = float(min_amount)

        if max_amount:
            # Como usamos abs() nos cálculos, filtramos considerando valores absolutos
            filters['amount__lte'] = float(max_amount)

        return TransactionModel.objects.filter(**filters).select_related('category').order_by('-date')

    def get_basic_stats(self, transactions):
        """Calcula estatísticas básicas das transações"""
        total_revenue = sum(abs(t.amount) for t in transactions if t.is_positive)
        total_expenses = sum(abs(t.amount) for t in transactions if not t.is_positive)
        net_balance = total_revenue - total_expenses

        transaction_count = len(transactions)
        avg_transaction = sum(t.amount for t in transactions) / transaction_count if transaction_count > 0 else 0

        # Top categorias
        category_totals = {}
        for t in transactions:
            cat_name = t.category.name if t.category else 'Sem Categoria'
            if cat_name not in category_totals:
                category_totals[cat_name] = 0
            category_totals[cat_name] += abs(t.amount)

        top_categories = sorted(category_totals.items(), key=lambda x: x[1], reverse=True)[:5]

        return {
            'total_revenue': total_revenue,
            'total_expenses': total_expenses,
            'net_balance': net_balance,
            'transaction_count': transaction_count,
            'avg_transaction': avg_transaction,
            'top_categories': top_categories,
        }

    def get_chart_data(self, transactions, start_date, end_date):
        """Prepara dados para gráficos"""
        # Dados mensais
        monthly_data = self.get_monthly_data(transactions, start_date, end_date)

        # Distribuição por categoria
        category_data = self.get_category_distribution(transactions)

        return {
            'monthly_data_json': json.dumps(monthly_data),
            'category_data_json': json.dumps(category_data),
        }

    def get_monthly_data(self, transactions, start_date, end_date):
        """Dados mensais de receitas vs despesas"""
        data = []

        # Agrupar transações por mês
        monthly_totals = {}
        for t in transactions:
            month_key = f"{t.date.year}-{t.date.month:02d}"
            if month_key not in monthly_totals:
                monthly_totals[month_key] = {'revenue': 0, 'expenses': 0}

            if t.is_positive:
                monthly_totals[month_key]['revenue'] += abs(float(t.amount))
            else:
                monthly_totals[month_key]['expenses'] += abs(float(t.amount))

        # Ordenar por mês
        for month in sorted(monthly_totals.keys()):
            data.append({
                'month': month,
                'revenue': monthly_totals[month]['revenue'],
                'expenses': monthly_totals[month]['expenses'],
                'net': monthly_totals[month]['revenue'] - monthly_totals[month]['expenses']
            })

        return data

    def get_category_distribution(self, transactions):
        """Distribuição de valores por categoria"""
        category_totals = {}
        for t in transactions:
            cat_name = t.category.name if t.category else 'Sem Categoria'
            if cat_name not in category_totals:
                category_totals[cat_name] = 0
            category_totals[cat_name] += abs(float(t.amount))

        return [{'category': cat, 'total': total} for cat, total in category_totals.items()]

    def get_available_categories(self):
        """Retorna lista de todas as categorias disponíveis"""
        categories = CategoryModel.objects.all().values_list('name', flat=True).order_by('name')
        return list(categories)

    def get_ai_insights(self, transactions, start_date, end_date):
        """Gera insights de AI baseados nos dados financeiros, com cache para persistência"""
        # Criar hash único baseado nos filtros e dados para cache
        data_hash = self._generate_data_hash(transactions, start_date, end_date)
        cache_key = f"financial_ai_insights_{data_hash}"

        # Verificar cache
        cached_insights = cache.get(cache_key)
        if cached_insights:
            return cached_insights

        # Gerar novos insights se não estiver em cache
        insights = self._generate_ai_insights(transactions, start_date, end_date)

        # Cache por 24 horas
        cache.set(cache_key, insights, 60*60*24)

        return insights

    def _generate_data_hash(self, transactions, start_date, end_date):
        """Gera hash único baseado nos dados para identificar mudanças"""
        # Usar datas e contagem de transações para o hash
        data_str = f"{start_date}_{end_date}_{len(transactions)}"
        if transactions:
            # Incluir algumas estatísticas básicas no hash
            total_amount = sum(t.amount for t in transactions)
            data_str += f"_{total_amount}"

        return hashlib.md5(data_str.encode()).hexdigest()

    def _generate_ai_insights(self, transactions, start_date, end_date):
        """Gera insights usando IA"""
        if not hasattr(settings, 'MISTRAL_API_KEY') or not settings.MISTRAL_API_KEY:
            return "Chave da API do Mistral não configurada."

        if not transactions:
            return "Sem dados suficientes para gerar insights."

        # Preparar dados resumidos para o prompt
        total_revenue = sum(abs(t.amount) for t in transactions if t.is_positive)
        total_expenses = sum(abs(t.amount) for t in transactions if not t.is_positive)
        net_balance = total_revenue - total_expenses
        transaction_count = len(transactions)

        # Top categorias de receitas e despesas separadamente
        revenue_categories = {}
        expense_categories = {}

        for t in transactions:
            cat_name = t.category.name if t.category else 'Sem Categoria'
            abs_amount = abs(t.amount)

            if t.is_positive:
                if cat_name not in revenue_categories:
                    revenue_categories[cat_name] = 0
                revenue_categories[cat_name] += abs_amount
            else:
                if cat_name not in expense_categories:
                    expense_categories[cat_name] = 0
                expense_categories[cat_name] += abs_amount

        top_revenue_categories = sorted(revenue_categories.items(), key=lambda x: x[1], reverse=True)[:3]
        top_expense_categories = sorted(expense_categories.items(), key=lambda x: x[1], reverse=True)[:3]

        # Calcular percentuais para melhor análise
        def format_category_list(categories, total, category_type):
            if not categories:
                return f"Sem {category_type.lower()} registradas"
            formatted = []
            for cat, amt in categories:
                percentage = (amt / total * 100) if total > 0 else 0
                formatted.append(f"{cat}: R$ {amt:.2f} ({percentage:.1f}%)")
            return f"Top {category_type}: {', '.join(formatted)}"

        revenue_summary = format_category_list(top_revenue_categories, total_revenue, "Receitas")
        expense_summary = format_category_list(top_expense_categories, total_expenses, "Despesas")

        prompt = f"""
        Analise os seguintes dados financeiros do período de {start_date} a {end_date}:

        - Total de Receitas: R$ {total_revenue:.2f}
        - Total de Despesas: R$ {total_expenses:.2f}
        - Saldo Líquido: R$ {net_balance:.2f}
        - Número de Transações: {transaction_count}
        - {revenue_summary}
        - {expense_summary}

        Forneça insights financeiros úteis em português, incluindo:
        1. Análise da saúde financeira
        2. Tendências identificadas (considere receitas vs despesas separadamente)
        3. Recomendações práticas
        4. Pontos de atenção

        Seja conciso mas informativo, limite a resposta a 300 palavras.
        """

        try:
            url = "https://api.mistral.ai/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {settings.MISTRAL_API_KEY}",
                "Content-Type": "application/json"
            }
            data = {
                "model": get_mistral_model_for_task("text"),
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 1000,
                "temperature": 0.7
            }

            response = requests.post(url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            result = response.json()
            return result['choices'][0]['message']['content']

        except Exception as e:
            return f"Erro ao gerar insights de IA: {str(e)}"

    def get(self, request, *args, **kwargs):
        # Se for uma requisição AJAX para insights de AI
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' and request.GET.get('action') == 'generate_insights':
            start_date = request.GET.get('start_date')
            end_date = request.GET.get('end_date')
            categories = request.GET.getlist('categories')
            transaction_type = request.GET.get('type')
            min_amount = request.GET.get('min_amount')
            max_amount = request.GET.get('max_amount')

            if start_date and end_date:
                transactions = self.get_filtered_transactions(
                    start_date, end_date, categories, transaction_type, min_amount, max_amount
                )
                insights = self.get_ai_insights(transactions, start_date, end_date)
                return JsonResponse({'insights': insights})

        return super().get(request, *args, **kwargs)