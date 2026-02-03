from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
import calendar


class AccountingPeriod(models.Model):
    """
    Período contábil para gerenciamento de fechamento mensal.

    Implementa o princípio contábil de período fiscal, onde os saldos
    são fixados ao fechamento e não podem mais ser alterados diretamente.
    """

    STATUS_CHOICES = [
        ('open', 'Aberto'),
        ('closed', 'Fechado'),
        ('archived', 'Arquivado'),
    ]

    # Primeiro dia do mês (ex: 2024-01-01 para janeiro de 2024)
    month = models.DateField(unique=True, help_text="Primeiro dia do mês de referência")

    # Marca se este é o primeiro período (saldo inicial de importação)
    is_first_month = models.BooleanField(
        default=False,
        help_text="Marca se este é o período inicial com saldo de importação"
    )

    # Status do período
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='open',
        help_text="Status atual do período"
    )

    # Saldo inicial (herdado do mês anterior ou definido manualmente)
    opening_balance = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Saldo inicial do período"
    )

    # Saldo final (fixado no fechamento - não pode ser alterado)
    closing_balance = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Saldo final fixado no fechamento"
    )

    # Metadados de fechamento
    closed_at = models.DateTimeField(null=True, blank=True)
    closed_by = models.ForeignKey(
        'users.CustomUser',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='closed_periods',
        help_text="Usuário que fechou o período"
    )

    # Observações do fechamento
    notes = models.TextField(blank=True, help_text="Observações sobre o fechamento")

    # Auditoria
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-month']
        verbose_name = 'período contábil'
        verbose_name_plural = 'períodos contábeis'
        indexes = [
            models.Index(fields=['month']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return self.month.strftime('%B/%Y').capitalize()

    @property
    def year(self):
        """Retorna o ano do período."""
        return self.month.year

    @property
    def month_number(self):
        """Retorna o número do mês (1-12)."""
        return self.month.month

    @property
    def month_name(self):
        """Retorna o nome do mês em português."""
        meses = [
            'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
            'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
        ]
        return meses[self.month.month - 1]

    @property
    def first_day(self):
        """Retorna o primeiro dia do mês."""
        return self.month.replace(day=1)

    @property
    def last_day(self):
        """Retorna o último dia do mês."""
        _, last_day = calendar.monthrange(self.month.year, self.month.month)
        return self.month.replace(day=last_day)

    @property
    def is_open(self):
        """Verifica se o período está aberto."""
        return self.status == 'open'

    @property
    def is_closed(self):
        """Verifica se o período está fechado."""
        return self.status == 'closed'

    @property
    def is_archived(self):
        """Verifica se o período está arquivado."""
        return self.status == 'archived'

    @property
    def is_current_month(self):
        """Verifica se este é o mês corrente (hoje)."""
        today = timezone.now().date()
        current_month = today.replace(day=1)
        return self.month == current_month

    @property
    def can_be_closed(self):
        """Verifica se o período pode ser fechado."""
        if self.status != 'open':
            return False
        # Mês corrente não pode ser fechado (ainda em andamento)
        if self.is_current_month:
            return False
        return True

    @property
    def can_be_reopened(self):
        """Verifica se o período pode ser reaberto."""
        return self.status in ['closed', 'archived']

    def clean(self):
        """Validações do modelo."""
        super().clean()

        # Verificar se o mês é realmente o primeiro dia
        if self.month.day != 1:
            raise ValidationError({
                'month': 'A data deve ser o primeiro dia do mês.'
            })

        # Não permitir datas futuras
        today = timezone.now().date()
        if self.month > today.replace(day=1):
            raise ValidationError({
                'month': 'Não é permitido criar períodos futuros.'
            })

        # Validações para is_first_month
        if self.is_first_month:
            # Não permitir períodos anteriores ao first_month
            previous_periods = AccountingPeriod.objects.filter(
                month__lt=self.month
            ).exclude(pk=self.pk)

            if previous_periods.exists():
                raise ValidationError({
                    'is_first_month': 'Não pode marcar como first_month se existem períodos anteriores. '
                                    'Este campo deve ser usado apenas no primeiro período do sistema '
                                    '(geralmente um mês de importação de saldo inicial).'
                })

        # Se não é first_month, verificar se já existe um first_month anterior
        # (para garantir consistência)
        if not self.is_first_month:
            first_month = AccountingPeriod.objects.filter(
                is_first_month=True
            ).exclude(pk=self.pk).first()

            if first_month and self.month < first_month.month:
                raise ValidationError({
                    'month': f'Já existe um período inicial ({first_month.month_name}/{first_month.year}). '
                             'Não é permitido criar períodos antes do período inicial.'
                })

    def close(self, user=None, notes=''):
        """
        Fecha o período contábil.

        Calcula o saldo final com base nas transações do período
        e fixa o valor para que não possa mais ser alterado.

        Cria automaticamente:
        - Um snapshot para preservar o relatório analítico
        - O MonthlyReportModel para gerar o PDF analítico

        Args:
            user: Usuário que está fechando o período
            notes: Observações sobre o fechamento

        Returns:
            O saldo final calculado
        """
        from treasury.services.transaction_service import TransactionService

        if not self.can_be_closed:
            raise ValueError('Apenas períodos abertos podem ser fechados.')

        # Calcular o saldo final
        service = TransactionService()
        final_balance = service.calculate_period_balance(self)

        # Atualizar o período
        self.closing_balance = final_balance
        self.status = 'closed'
        self.closed_at = timezone.now()
        self.closed_by = user
        self.notes = notes
        self.save(update_fields=['closing_balance', 'status', 'closed_at', 'closed_by', 'notes'])

        # Criar snapshot automaticamente para preservar o relatório analítico
        from treasury.models.period_snapshot import PeriodSnapshot
        PeriodSnapshot.create_from_period(
            self,
            created_by=user,
            reason=f'Fechamento do período {self.month_name}/{self.year}'
        )

        # Criar automaticamente o MonthlyReportModel para o PDF analítico
        self._create_monthly_report()

        # Criar FrozenReport com o PDF analítico para auditoria
        self._create_frozen_reports(user)

        # Atualizar ou criar o próximo período com o saldo correto
        next_month = self.get_next_month()
        if next_month:
            next_period, created = AccountingPeriod.objects.get_or_create(
                month=next_month,
                defaults={
                    'opening_balance': final_balance,
                    'status': 'open'
                }
            )
            # Se já existe, atualizar o opening_balance
            if not created:
                next_period.opening_balance = final_balance
                next_period.save(update_fields=['opening_balance'])

        return final_balance

    def _create_monthly_report(self):
        """
        Cria o MonthlyReportModel automaticamente ao fechar o período.
        """
        from .monthly_report_model import MonthlyReportModel
        from .transaction import TransactionModel
        from decimal import Decimal

        year = self.month.year
        month = self.month.month

        # Buscar período anterior para obter o saldo inicial
        prev_period = self.get_previous_period()
        previous_balance = Decimal('0.00')
        if prev_period:
            if prev_period.closing_balance:
                previous_balance = prev_period.closing_balance
            else:
                previous_balance = prev_period.get_current_balance()

        # Calcular totais das transações
        transactions = TransactionModel.objects.filter(
            accounting_period=self,
            transaction_type='original'
        )

        positive = transactions.filter(is_positive=True).aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0.00')

        negative = transactions.filter(is_positive=False).aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0.00')

        # Calcular totais por categoria (para o relatório)
        positive_by_category = {}
        for tx in transactions.filter(is_positive=True):
            cat_name = tx.category.name if tx.category else 'outros'
            positive_by_category[cat_name] = positive_by_category.get(cat_name, Decimal('0.00')) + tx.amount

        negative_by_category = {}
        for tx in transactions.filter(is_positive=False):
            cat_name = tx.category.name if tx.category else 'outros'
            negative_by_category[cat_name] = negative_by_category.get(cat_name, Decimal('0.00')) + tx.amount

        # Calcular campos específicos (ajuste conforme necessário)
        in_cash = Decimal('0.00')  # TODO: calcular com base nas transações
        in_current_account = Decimal('0.00')  # TODO: calcular com base nas transações
        in_savings_account = Decimal('0.00')  # TODO: calcular com base nas transações

        # negative já é negativo (amount armazena valores com sinal)
        monthly_result = positive + negative
        total_balance = previous_balance + monthly_result

        # Criar ou atualizar o MonthlyReportModel
        report, created = MonthlyReportModel.objects.get_or_create(
            month=self.month,
            defaults={
                'previous_month_balance': previous_balance,
                'total_positive_transactions': positive,
                'total_negative_transactions': negative,
                'in_cash': in_cash,
                'in_current_account': in_current_account,
                'in_savings_account': in_savings_account,
                'monthly_result': monthly_result,
                'total_balance': total_balance,
            }
        )

        # Se já existe, atualizar
        if not created:
            report.previous_month_balance = previous_balance
            report.total_positive_transactions = positive
            report.total_negative_transactions = negative
            report.in_cash = in_cash
            report.in_current_account = in_current_account
            report.in_savings_account = in_savings_account
            report.monthly_result = monthly_result
            report.total_balance = total_balance
            report.save()

    def _create_frozen_reports(self, user=None):
        """
        Cria FrozenReports com PDFs para auditoria.

        Gera os PDFs (analítico e extrato) e os armazena com hash SHA256
        para garantir integridade.
        """
        from treasury.models import FrozenReport
        from django.template.loader import render_to_string
        import weasyprint

        year = self.month.year
        month = self.month.month

        # Preparar contexto para os PDFs
        from treasury.utils import get_aggregate_transactions_by_category, get_last_day_of_month
        from core.core_context_processor import context_user_data
        from decimal import Decimal

        # Dados do relatório
        an_report = MonthlyReportModel.objects.filter(month=self.month).first()
        if not an_report:
            return

        last_day = get_last_day_of_month(year, month)

        positive_transactions_dict = get_aggregate_transactions_by_category(year, month, True)
        negative_transactions_dict = get_aggregate_transactions_by_category(year, month, False)

        m_result = an_report.total_positive_transactions + an_report.total_negative_transactions

        # Contexto básico (sem request, então sem church_info)
        context = {
            "date": last_day,
            "year": year,
            "month": month,
            "pm_balance": an_report.previous_month_balance,
            "report": an_report,
            "p_transactions": positive_transactions_dict,
            "n_transactions": negative_transactions_dict,
            "total_p": an_report.total_positive_transactions,
            "total_n": an_report.total_negative_transactions,
            "m_result": m_result,
            "balance": Decimal(an_report.total_balance),
        }

        # Gerar PDF Analítico
        try:
            html_analytical = render_to_string("treasury/export_analytical_report.html", context)
            pdf_analytical = weasyprint.HTML(string=html_analytical).write_pdf()

            FrozenReport.create_from_period(
                period=self,
                pdf_bytes=pdf_analytical,
                report_type='analytical',
                user=user
            )
        except Exception as e:
            # Log mas não falha o fechamento
            import logging
            logging.getLogger(__name__).error(f"Erro ao criar FrozenReport analítico: {e}")

        # Gerar PDF Extrato
        try:
            from treasury.models import TransactionModel

            # Buscar todas as transações do período
            transactions = TransactionModel.objects.filter(
                accounting_period=self,
                transaction_type='original'
            ).order_by('date', 'created_at')

            # Contexto para o extrato
            extract_context = {
                "date": last_day,
                "year": year,
                "month": month,
                "pm_balance": an_report.previous_month_balance,
                "total_p": an_report.total_positive_transactions,
                "total_n": an_report.total_negative_transactions,
                "m_result": m_result,
                "balance": Decimal(an_report.total_balance),
                "transactions": transactions,
                "transaction_count": transactions.count(),
            }

            html_extract = render_to_string("treasury/export_extract_report.html", extract_context)
            pdf_extract = weasyprint.HTML(string=html_extract).write_pdf()

            FrozenReport.create_from_period(
                period=self,
                pdf_bytes=pdf_extract,
                report_type='extract',
                user=user
            )
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Erro ao criar FrozenReport extrato: {e}")

    def reopen(self, user=None):
        """
        Reabre um período fechado.

        Apenas períodos fechados ou arquivados podem ser reabertos.
        Ao reabrir, o saldo final é limpo.

        Args:
            user: Usuário que está reabrindo o período
        """
        if not self.can_be_reopened:
            raise ValueError('Apenas períodos fechados ou arquivados podem ser reabertos.')

        self.status = 'open'
        self.closing_balance = None
        self.closed_at = None
        self.closed_by = None
        self.notes = ''
        self.save(update_fields=['status', 'closing_balance', 'closed_at', 'closed_by', 'notes'])

    def archive(self):
        """Arquiva o período (período fechado que não será mais modificado)."""
        if self.status != 'closed':
            raise ValueError('Apenas períodos fechados podem ser arquivados.')

        self.status = 'archived'
        self.save(update_fields=['status'])

    def get_previous_period(self):
        """Retorna o período anterior."""
        # Calcular o mês anterior
        if self.month.month == 1:
            prev_month = self.month.replace(year=self.month.year - 1, month=12, day=1)
        else:
            prev_month = self.month.replace(month=self.month.month - 1, day=1)

        try:
            return AccountingPeriod.objects.get(month=prev_month)
        except AccountingPeriod.DoesNotExist:
            return None

    def get_next_month(self):
        """Retorna a data do primeiro dia do mês seguinte."""
        if self.month.month == 12:
            return self.month.replace(year=self.month.year + 1, month=1, day=1)
        else:
            return self.month.replace(month=self.month.month + 1, day=1)

    def get_next_period(self):
        """Retorna o próximo período."""
        next_month_date = self.get_next_month()
        try:
            return AccountingPeriod.objects.get(month=next_month_date)
        except AccountingPeriod.DoesNotExist:
            return None

    def get_current_balance(self):
        """
        Retorna o saldo atual do período.

        Se o período estiver fechado, retorna o closing_balance.
        Se estiver aberto, calcula o saldo dinâmico.
        """
        if self.is_closed:
            return self.closing_balance

        from treasury.services.transaction_service import TransactionService
        service = TransactionService()
        return service.calculate_period_balance(self)

    def get_transactions_summary(self):
        """
        Retorna um resumo das transações do período.

        Nota: amount é sempre positivo, o sinal é determinado por is_positive.
        """
        from treasury.models.transaction import TransactionModel

        transactions = TransactionModel.objects.filter(
            accounting_period=self,
            transaction_type='original'
        )

        # Somar positivas
        positive = transactions.filter(is_positive=True).aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0.00')

        # Somar negativas (amount já é negativo para transações negativas)
        negative = transactions.filter(is_positive=False).aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0.00')

        # Net = positivas + negativas (negative já é negativo)
        net = positive + negative

        return {
            'total_positive': positive,
            'total_negative': negative,
            'net': net,
            'count': transactions.count(),
        }
