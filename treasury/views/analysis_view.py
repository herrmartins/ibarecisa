from django.views.generic import TemplateView
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db.models import Sum, Q, Count
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from treasury.models import TransactionModel, CategoryModel, MonthlyBalance
from django.http import JsonResponse
from django.core.cache import cache
from secretarial.utils.ai_utils import get_mistral_model_for_task
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
import json
import requests
from django.conf import settings
import hashlib
import logging


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

        # Transações paginadas para exibição na lista
        page = self.request.GET.get('page', 1)
        paginator = Paginator(transactions, 20)  # 20 transações por página

        try:
            paginated_transactions = paginator.page(page)
        except PageNotAnInteger:
            paginated_transactions = paginator.page(1)
        except EmptyPage:
            paginated_transactions = paginator.page(paginator.num_pages)

        context['paginated_transactions'] = paginated_transactions

        # Data de geração dos insights
        context['insights_generated_at'] = timezone.now()

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

        # Garantir que não há valores None nos dados
        def clean_data(data):
            if isinstance(data, list):
                return [clean_data(item) for item in data]
            elif isinstance(data, dict):
                return {k: clean_data(v) for k, v in data.items()}
            elif data is None:
                return 0  # Substituir None por 0
            else:
                return data

        monthly_data = clean_data(monthly_data)
        category_data = clean_data(category_data)

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
        Analise os seguintes dados financeiros do período de {start_date} a {end_date} como um analista financeiro cristão responsável pelos recursos da igreja:

        DADOS FINANCEIROS:
        - Total de Receitas: R$ {total_revenue:.2f}
        - Total de Despesas: R$ {total_expenses:.2f}
        - Saldo Líquido: R$ {net_balance:.2f}
        - Número de Transações: {transaction_count}
        - {revenue_summary}
        - {expense_summary}

        Forneça uma análise equilibrada em português contendo:

        1. ANÁLISE ECONÔMICA: Identifique tendências importantes, eficiência financeira, distribuição de gastos e pontos de atenção nos dados.

        2. RECOMENDAÇÕES PRÁTICAS: Sugira ações concretas para melhorar a gestão financeira da igreja.

        3. PERSPECTIVA ESPIRITUAL: Relacione os dados financeiros com princípios bíblicos, citando versículos relevantes como:
           - 1 Coríntios 4:2 (fidelidade nos recursos de Deus)
           - Provérbios 24:3-4 (sabedoria na administração)
           - Mateus 6:19-21 (tesouros no céu)
           - Filipenses 4:19 (Deus supre todas as necessidades)

        4. ENCORAJAMENTO: Incentive a dependência em Deus e a gratidão pelas bênçãos recebidas.

        Seja objetivo nos aspectos técnicos e encorajador na orientação espiritual. Limite a resposta a 500 palavras.
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

    def dispatch(self, request, *args, **kwargs):
        """
        Tratamento direto de requisições AJAX de geração de insights para garantir
        que retornemos JSON (evitando redirecionamentos HTML do PermissionRequiredMixin).
        Inclui rota de diagnóstico temporária `diagnose=1` para retornar informações
        úteis na depuração (não expõe dados sensíveis).
        """
        logger = logging.getLogger(__name__)
        action = request.GET.get('action')
        # Log básico para diagnóstico
        try:
            logger.debug("dispatch start: action=%s, user=%s, is_authenticated=%s",
                         action, getattr(request.user, 'username', None), request.user.is_authenticated)
        except Exception:
            pass

        # Rota de diagnóstico temporária (ativa apenas quando solicitada)
        if action == 'generate_insights' and request.GET.get('diagnose') == '1':
            # Preparar objeto de diagnóstico para o front-end (não incluir valores sensíveis)
            diag = {
                'is_authenticated': bool(request.user and request.user.is_authenticated),
                'username': getattr(request.user, 'username', None),
                'has_permission': request.user.has_perm(self.permission_required) if getattr(request.user, 'is_authenticated', False) else False,
                'headers': {
                    'x_requested_with': request.META.get('HTTP_X_REQUESTED_WITH'),
                    'content_type': request.META.get('CONTENT_TYPE'),
                },
                'cookies_present': list(request.COOKIES.keys()),
                'session_key': request.session.session_key if hasattr(request, 'session') else None,
                'get_params': {k: v for k, v in request.GET.items()},
            }
            logger.info("AJAX-insights diagnostic requested by user=%s", getattr(request.user, 'username', None))
            return JsonResponse({'diagnostic': diag})

        # Tratar internamente a geração de insights e retornar JSON para AJAX
        if action == 'generate_insights':
            # Autenticação e permissão
            if not request.user.is_authenticated:
                logger.warning("AJAX-insights unauthenticated request detected.")
                return JsonResponse({
                    'error': 'Sessão expirada ou acesso negado. Recarregue a página e faça login novamente.'
                }, status=401)

            if not request.user.has_perm(self.permission_required):
                logger.warning("AJAX-insights permission denied for user=%s", getattr(request.user, 'username', None))
                return JsonResponse({
                    'error': 'Você não tem permissão para acessar esta funcionalidade.'
                }, status=403)

            # Extrair parâmetros e gerar insights diretamente aqui
            start_date = request.GET.get('start_date')
            end_date = request.GET.get('end_date')
            categories = request.GET.getlist('categories')
            transaction_type = request.GET.get('type')
            min_amount = request.GET.get('min_amount')
            max_amount = request.GET.get('max_amount')

            # Se datas ausentes, padronizar para últimos 12 meses (mesma lógica do get_context_data)
            if not start_date or not end_date:
                end_date = timezone.now().date()
                start_date = end_date - relativedelta(months=12)

            try:
                transactions = self.get_filtered_transactions(
                    start_date, end_date, categories, transaction_type, min_amount, max_amount
                )
                insights = self.get_ai_insights(transactions, start_date, end_date)
                return JsonResponse({'insights': insights})
            except Exception as e:
                logger.exception("Erro ao gerar insights via AJAX: %s", e)
                return JsonResponse({
                    'error': f'Erro ao processar insights: {str(e)}'
                }, status=500)

        # Fluxo normal para requests não-AJAX
        return super().dispatch(request, *args, **kwargs)
    
    
    def get(self, request, *args, **kwargs):
        """
        Tratamento de GET para geração de insights via AJAX.
        Unifica o comportamento com `dispatch` para garantir que quando
        `action=generate_insights` sempre retornemos JSON (mesmo que faltem
        parâmetros de data) e não a página HTML.
        """
        action = request.GET.get('action')
        if action == 'generate_insights':
            # Autenticação e permissão
            if not request.user.is_authenticated:
                return JsonResponse({
                    'error': 'Sessão expirada ou acesso negado. Recarregue a página e faça login novamente.'
                }, status=401)

            if not request.user.has_perm(self.permission_required):
                return JsonResponse({
                    'error': 'Você não tem permissão para acessar esta funcionalidade.'
                }, status=403)

            # Extrair parâmetros (usar valores padrão se ausentes)
            start_date = request.GET.get('start_date')
            end_date = request.GET.get('end_date')
            categories = request.GET.getlist('categories')
            transaction_type = request.GET.get('type')
            min_amount = request.GET.get('min_amount')
            max_amount = request.GET.get('max_amount')

            if not start_date or not end_date:
                end_date = timezone.now().date()
                start_date = end_date - relativedelta(months=12)

            try:
                transactions = self.get_filtered_transactions(
                    start_date, end_date, categories, transaction_type, min_amount, max_amount
                )
                insights = self.get_ai_insights(transactions, start_date, end_date)
                return JsonResponse({'insights': insights})
            except Exception as e:
                logger = logging.getLogger(__name__)
                logger.exception("Erro ao processar insights via GET: %s", e)
                return JsonResponse({
                    'error': f'Erro ao processar insights: {str(e)}'
                }, status=500)

        return super().get(request, *args, **kwargs)