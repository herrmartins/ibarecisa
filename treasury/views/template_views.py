"""
Django Views para renderização de templates (não-API).

Estas views complementam a API REST Framework, fornecendo
templates renderizados no servidor com interatividade via Alpine.js.
"""

from django.views.generic import TemplateView, ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from datetime import datetime, timedelta

from treasury.models import AccountingPeriod, TransactionModel, CategoryModel


class TreasuryDashboardView(LoginRequiredMixin, TemplateView):
    """Dashboard principal da tesouraria."""
    template_name = 'treasury/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Dados serão carregados via API/Fetch no frontend
        context['page_title'] = 'Dashboard'
        return context


class PeriodListView(LoginRequiredMixin, ListView):
    """Lista de períodos contábeis."""
    model = AccountingPeriod
    template_name = 'treasury/periods/list.html'
    context_object_name = 'periods'
    paginate_by = 12

    def get_queryset(self):
        return AccountingPeriod.objects.all().order_by('-month')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Períodos Contábeis'
        return context


class PeriodDetailView(LoginRequiredMixin, DetailView):
    """Detalhes de um período contábil."""
    model = AccountingPeriod
    template_name = 'treasury/periods/detail.html'
    context_object_name = 'period'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Período: {self.object.month_name}'
        # Transações serão carregadas via API
        return context


class TransactionListView(LoginRequiredMixin, TemplateView):
    """Lista de transações com filtros."""
    template_name = 'treasury/transactions/list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Transações'
        context['categories'] = CategoryModel.objects.all().order_by('name')
        return context


class TransactionDetailView(LoginRequiredMixin, DetailView):
    """Detalhes de uma transação."""
    model = TransactionModel
    template_name = 'treasury/transactions/detail.html'
    context_object_name = 'transaction'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Transação: {self.object.description}'
        return context


class TransactionCreateView(LoginRequiredMixin, CreateView):
    """Formulário para criar nova transação."""
    model = TransactionModel
    template_name = 'treasury/transactions/form.html'
    fields = ['category', 'description', 'amount', 'is_positive', 'date', 'acquittance_doc']

    def get_success_url(self):
        return reverse_lazy('treasury:transaction-detail-new', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Nova Transação'
        context['categories'] = CategoryModel.objects.all().order_by('name')
        context['is_create'] = True
        return context

    def form_valid(self, form):
        form.instance.user = self.request.user
        form.instance.created_by = self.request.user
        # O período será definido automaticamente no save do modelo
        return super().form_valid(form)


class TransactionUpdateView(LoginRequiredMixin, UpdateView):
    """Formulário para editar transação."""
    model = TransactionModel
    template_name = 'treasury/transactions/update.html'
    fields = ['category', 'description', 'amount', 'is_positive', 'date', 'acquittance_doc']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Editar: {self.object.description}'
        context['categories'] = CategoryModel.objects.all().order_by('name')
        context['is_create'] = False
        context['can_edit'] = self.object.can_be_edited
        return context

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if not obj.can_be_edited:
            # Redirecionar para página de estorno se período fechado
            return redirect('treasury:transaction-reversal', pk=obj.pk)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('treasury:transaction-detail-new', kwargs={'pk': self.object.pk})


class CategoryListView(LoginRequiredMixin, ListView):
    """Lista de categorias."""
    model = CategoryModel
    template_name = 'treasury/categories/list.html'
    context_object_name = 'categories'

    def get_queryset(self):
        return CategoryModel.objects.all().order_by('name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Categorias'
        return context


class MonthlyReportView(LoginRequiredMixin, TemplateView):
    """Relatório mensal detalhado."""
    template_name = 'treasury/reports/monthly.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        year = self.kwargs.get('year', timezone.now().year)
        month = self.kwargs.get('month', timezone.now().month)

        try:
            period = AccountingPeriod.objects.get(
                month__year=year,
                month__month=month
            )
            context['period'] = period
            context['page_title'] = f'Relatório: {period.month_name} de {year}'
        except AccountingPeriod.DoesNotExist:
            context['period'] = None
            context['page_title'] = 'Relatório Mensal'
            context['year'] = year
            context['month'] = month

        return context


class ReversalView(LoginRequiredMixin, DetailView):
    """View para criar estorno de transação."""
    model = TransactionModel
    template_name = 'treasury/transactions/reversal.html'
    context_object_name = 'transaction'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Estornar: {self.object.description}'
        context['categories'] = CategoryModel.objects.all().order_by('name')
        return context

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.can_be_edited:
            # Se pode editar, redirecionar para edição normal
            return redirect('treasury:transaction-update-new', pk=obj.pk)
        return super().dispatch(request, *args, **kwargs)


class BalanceSheetView(LoginRequiredMixin, TemplateView):
    """Balanço financeiro."""
    template_name = 'treasury/reports/balance_sheet.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Balanço Financeiro'
        context['periods'] = AccountingPeriod.objects.all().order_by('-month')[:12]
        return context
