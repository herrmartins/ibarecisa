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
    def can_be_closed(self):
        """Verifica se o período pode ser fechado."""
        return self.status == 'open'

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

    def close(self, user=None, notes=''):
        """
        Fecha o período contábil.

        Calcula o saldo final com base nas transações do período
        e fixa o valor para que não possa mais ser alterado.

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

        # Criar o próximo período se não existir
        next_month = self.get_next_month()
        if next_month and not AccountingPeriod.objects.filter(month=next_month).exists():
            AccountingPeriod.objects.create(
                month=next_month,
                opening_balance=final_balance,
                status='open'
            )

        return final_balance

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

        Nota: As transações negativas têm amount armazenado como valor negativo.
        """
        from treasury.models.transaction import TransactionModel

        transactions = TransactionModel.objects.filter(
            accounting_period=self,
            transaction_type='original'
        )

        # Somar positivas e negativas separadamente (valores absolutos para exibição)
        positive = transactions.filter(is_positive=True).aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0.00')

        # Para negativas, pegar o valor absoluto dos amounts (que são armazenados como negativos)
        negative_abs = transactions.filter(is_positive=False).aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0.00')
        negative = abs(negative_abs) if negative_abs else Decimal('0.00')

        # Net é a soma real (já inclui sinais)
        net = transactions.aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0.00')

        return {
            'total_positive': positive,
            'total_negative': negative,
            'net': net,
            'count': transactions.count(),
        }
