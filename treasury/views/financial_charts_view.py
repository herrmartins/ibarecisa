from django.views.generic import TemplateView
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db.models import Sum, Q
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from treasury.models import TransactionModel, CategoryModel, MonthlyBalance
from django.http import JsonResponse
import json


class FinancialChartsView(PermissionRequiredMixin, TemplateView):
    permission_required = "treasury.view_transactionmodel"
    template_name = "treasury/financial_charts.html"

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

        # Dados para os gráficos
        chart_data = self.get_chart_data(start_date, end_date)
        context.update(chart_data)

        return context

    def get_chart_data(self, start_date, end_date):
        """Retorna dados agregados para os gráficos"""
        # Gráfico de linhas: Receitas vs Despesas vs Saldo
        monthly_data = self.get_monthly_revenue_expense_data(start_date, end_date)

        # Gráficos de pizza: Distribuição por categoria (Receitas e Despesas)
        revenue_category_data = self.get_category_distribution_data(start_date, end_date, is_positive=True)
        expense_category_data = self.get_category_distribution_data(start_date, end_date, is_positive=False)

        return {
            'monthly_data_json': json.dumps(monthly_data),
            'revenue_category_data_json': json.dumps(revenue_category_data),
            'expense_category_data_json': json.dumps(expense_category_data),
        }

    def get_monthly_revenue_expense_data(self, start_date, end_date):
        """Dados mensais de receitas, despesas e saldo acumulado"""
        data = []

        # Converter strings para objetos date se necessário
        if isinstance(start_date, str):
            from datetime import datetime
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        if isinstance(end_date, str):
            from datetime import datetime
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

        # Obter todos os saldos mensais no período
        balances = MonthlyBalance.objects.filter(
            month__gte=start_date.replace(day=1),
            month__lte=end_date.replace(day=1)
        ).order_by('month')

        cumulative_balance = 0
        for balance in balances:
            month_start = balance.month
            month_end = (month_start + relativedelta(months=1)) - relativedelta(days=1)

            # Receitas do mês
            revenue = TransactionModel.objects.filter(
                date__gte=month_start,
                date__lte=month_end,
                is_positive=True
            ).aggregate(total=Sum('amount'))['total'] or 0

            # Despesas do mês
            expense = TransactionModel.objects.filter(
                date__gte=month_start,
                date__lte=month_end,
                is_positive=False
            ).aggregate(total=Sum('amount'))['total'] or 0

            cumulative_balance = balance.balance

            data.append({
                'month': f"{month_start.year}-{month_start.month:02d}",
                'revenue': float(revenue),
                'expense': float(expense),
                'balance': float(cumulative_balance)
            })

        return data

    def get_category_distribution_data(self, start_date, end_date, is_positive=None):
        """Distribuição de transações por categoria"""
        # Converter strings para objetos date se necessário
        if isinstance(start_date, str):
            from datetime import datetime
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        if isinstance(end_date, str):
            from datetime import datetime
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

        # Filtrar por tipo se especificado
        filters = {
            'date__gte': start_date,
            'date__lte': end_date,
            'category__isnull': False
        }

        if is_positive is not None:
            filters['is_positive'] = is_positive

        # Agrupar por categoria e somar valores absolutos
        category_totals = TransactionModel.objects.filter(**filters).values('category__name').annotate(
            total=Sum('amount')
        ).order_by('-total')

        data = []
        for item in category_totals:
            data.append({
                'category': item['category__name'],
                'total': float(item['total'])
            })

        return data

    def get(self, request, *args, **kwargs):
        # Se for uma requisição AJAX para dados JSON
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            start_date = request.GET.get('start_date')
            end_date = request.GET.get('end_date')

            if start_date and end_date:
                chart_data = self.get_chart_data(start_date, end_date)
                return JsonResponse(chart_data)

        return super().get(request, *args, **kwargs)