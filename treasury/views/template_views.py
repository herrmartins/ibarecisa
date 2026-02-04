"""
Django Views para renderização de templates (não-API).

Estas views complementam a API REST Framework, fornecendo
templates renderizados no servidor com interatividade via Alpine.js.
"""

import json
from django.views.generic import TemplateView, ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from datetime import datetime, timedelta

from treasury.models import AccountingPeriod, TransactionModel, CategoryModel, AuditLog
from treasury.mixins import IsTreasuryUserMixin, IsTreasurerOnlyMixin, IsSuperUserOnlyMixin


class TreasuryDashboardView(IsTreasuryUserMixin, LoginRequiredMixin, TemplateView):
    """Dashboard principal da tesouraria."""
    template_name = 'treasury/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Dados serão carregados via API/Fetch no frontend
        context['page_title'] = 'Dashboard'
        return context


class PeriodListView(IsTreasuryUserMixin, LoginRequiredMixin, ListView):
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


class PeriodDetailView(IsTreasuryUserMixin, LoginRequiredMixin, DetailView):
    """Detalhes de um período contábil."""
    model = AccountingPeriod
    template_name = 'treasury/periods/detail.html'
    context_object_name = 'period'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Período: {self.object.month_name}'
        # Transações serão carregadas via API
        return context


class TransactionListView(IsTreasuryUserMixin, LoginRequiredMixin, TemplateView):
    """Lista de transações com filtros."""
    template_name = 'treasury/transactions/list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Transações'
        context['categories'] = CategoryModel.objects.all().order_by('name')
        return context


class TransactionDetailView(IsTreasuryUserMixin, LoginRequiredMixin, DetailView):
    """Detalhes de uma transação."""
    model = TransactionModel
    template_name = 'treasury/transactions/detail.html'
    context_object_name = 'transaction'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Transação: {self.object.description}'
        return context


class TransactionCreateView(IsTreasurerOnlyMixin, LoginRequiredMixin, CreateView):
    """Formulário para criar nova transação (apenas tesoureiros)."""
    model = TransactionModel
    template_name = 'treasury/transactions/form.html'
    fields = ['category', 'description', 'amount', 'is_positive', 'date', 'acquittance_doc']

    def get_success_url(self):
        return reverse_lazy('treasury:transaction-detail', kwargs={'pk': self.object.pk})

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


class TransactionUpdateView(IsTreasurerOnlyMixin, LoginRequiredMixin, UpdateView):
    """Formulário para editar transação (apenas tesoureiros)."""
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
        return reverse_lazy('treasury:transaction-detail', kwargs={'pk': self.object.pk})


class TransactionDeleteView(IsSuperUserOnlyMixin, LoginRequiredMixin, DeleteView):
    """View para deletar transação (apenas superusuários)."""
    model = TransactionModel
    template_name = 'treasury/transactions/delete.html'
    context_object_name = 'transaction'
    success_url = reverse_lazy('treasury:transaction-list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Excluir: {self.object.description}'
        return context

    def delete(self, request, *args, **kwargs):
        """Sobrescreve para adicionar log de auditoria e tratar erros."""
        from django.contrib import messages
        from django.urls import reverse
        import logging
        logger = logging.getLogger(__name__)

        try:
            self.object = self.get_object()
            logger.info(f"[DELETE] Transação {self.object.id} encontrada, can_be_deleted={self.object.can_be_deleted}")
        except Exception as e:
            logger.error(f"[DELETE] Erro ao buscar transação: {e}", exc_info=True)
            messages.error(request, f'Transação não encontrada.')
            return redirect(reverse('treasury:dashboard'))

        if not self.object.can_be_deleted:
            messages.error(request, 'Esta transação não pode ser excluída porque o período está fechado.')
            return redirect(reverse('treasury:transaction-detail', kwargs={'pk': self.object.pk}))

        # Guarda info para mensagem de sucesso (antes de deletar)
        transaction_id = self.object.id
        transaction_desc = self.object.description

        # Log de auditoria antes de deletar
        try:
            AuditLog.log(
                action='transaction_deleted',
                entity_type='TransactionModel',
                entity_id=self.object.id,
                user=request.user,
                old_values={
                    'description': self.object.description,
                    'amount': str(self.object.amount),
                    'category': self.object.category.name if self.object.category else None,
                    'date': str(self.object.date),
                    'is_positive': self.object.is_positive,
                }
            )
            logger.info(f"[DELETE] Log de auditoria criado para transação {transaction_id}")
        except Exception as log_error:
            logger.error(f"[DELETE] Erro ao criar log de auditoria: {log_error}", exc_info=True)

        # Adiciona mensagem de sucesso ANTES de deletar
        messages.success(request, f'Transação #{transaction_id} "{transaction_desc}" excluída com sucesso.')

        # Tenta deletar
        try:
            logger.info(f"[DELETE] Chamando super().delete() para transação {transaction_id}")
            result = super().delete(request, *args, **kwargs)
            logger.info(f"[DELETE] Deleção concluída com sucesso")
            return result
        except Exception as e:
            logger.error(f"[DELETE] Erro ao deletar transação {transaction_id}: {e}", exc_info=True)
            messages.error(request, f'Erro ao excluir transação: {str(e)}')
            return redirect(reverse('treasury:transaction-detail', kwargs={'pk': self.object.pk}))


class BatchTransactionReviewView(IsTreasurerOnlyMixin, LoginRequiredMixin, TemplateView):
    """Página para revisar múltiplas transações extraídas via OCR (apenas tesoureiros)."""
    template_name = 'treasury/transactions/batch-review.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Revisar Transações'
        return context


class CategoryListView(IsTreasuryUserMixin, LoginRequiredMixin, ListView):
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


class MonthlyReportView(IsTreasuryUserMixin, LoginRequiredMixin, TemplateView):
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


class ReversalView(IsTreasurerOnlyMixin, LoginRequiredMixin, DetailView):
    """View para criar estorno de transação (apenas tesoureiros)."""
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
            return redirect('treasury:transaction-update', pk=obj.pk)
        return super().dispatch(request, *args, **kwargs)


class BalanceSheetView(IsTreasuryUserMixin, LoginRequiredMixin, TemplateView):
    """Balanço financeiro."""
    template_name = 'treasury/reports/balance_sheet.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Balanço Financeiro'
        context['periods'] = AccountingPeriod.objects.all().order_by('-month')[:12]
        return context


class AuditLogView(IsTreasuryUserMixin, LoginRequiredMixin, TemplateView):
    """Página de auditoria com filtros."""
    template_name = 'treasury/audit.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Auditoria'

        # Opções de filtro - converter para listas (JavaScript arrays)
        # json.dumps com ensure_ascii=False para preservar caracteres especiais
        context['action_choices'] = json.dumps(AuditLog.ACTION_CHOICES, ensure_ascii=False)
        context['entity_type_choices'] = json.dumps(AuditLog.ENTITY_TYPE_CHOICES, ensure_ascii=False)

        return context


class ChartsView(IsTreasuryUserMixin, LoginRequiredMixin, TemplateView):
    """Página de gráficos financeiros."""
    template_name = 'treasury/charts.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Gráficos'
        return context
