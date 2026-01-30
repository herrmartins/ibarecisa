from django.db.models import Sum, Q, Count, DecimalField
from django.db.models.functions import Coalesce
from django.utils import timezone
from decimal import Decimal
from datetime import datetime, date

from treasury.models import AccountingPeriod, TransactionModel


class PeriodService:
    """
    Serviço para lógica de negócio relacionada a períodos contábeis.

    Responsável por:
    - Fechamento de períodos
    - Cálculo de saldos
    - Validação de edições
    - Geração de relatórios
    """

    def close_period(self, period_id, user_id=None, notes=''):
        """
        Fecha um período contábil.

        Processo:
        1. Valida que o período está aberto
        2. Calcula o saldo final
        3. Atualiza o período
        4. Cria o próximo período se não existir

        Args:
            period_id: ID do período a ser fechado
            user_id: ID do usuário que está fechando
            notes: Observações sobre o fechamento

        Returns:
            O saldo final calculado

        Raises:
            ValueError: Se o período não puder ser fechado
        """
        try:
            period = AccountingPeriod.objects.get(id=period_id)
        except AccountingPeriod.DoesNotExist:
            raise ValueError('Período não encontrado.')

        if not period.can_be_closed:
            raise ValueError('Apenas períodos abertos podem ser fechados.')

        # Calcular o saldo final
        final_balance = self.calculate_period_balance(period)

        # Atualizar o período
        from django.contrib.auth import get_user_model
        User = get_user_model()

        user = None
        if user_id:
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                pass

        period.closing_balance = final_balance
        period.status = 'closed'
        period.closed_at = timezone.now()
        period.closed_by = user
        period.notes = notes
        period.save(update_fields=['closing_balance', 'status', 'closed_at', 'closed_by', 'notes'])

        # Criar o próximo período se não existir
        next_month = period.get_next_month()
        if next_month:
            AccountingPeriod.objects.get_or_create(
                month=next_month,
                defaults={
                    'opening_balance': final_balance,
                    'status': 'open'
                }
            )

        return final_balance

    def reopen_period(self, period_id, user_id=None):
        """
        Reabre um período fechado.

        Args:
            period_id: ID do período a ser reaberto
            user_id: ID do usuário que está reabrindo

        Returns:
            O período reaberto

        Raises:
            ValueError: Se o período não puder ser reaberto
        """
        try:
            period = AccountingPeriod.objects.get(id=period_id)
        except AccountingPeriod.DoesNotExist:
            raise ValueError('Período não encontrado.')

        if not period.can_be_reopened:
            raise ValueError('Apenas períodos fechados ou arquivados podem ser reabertos.')

        period.status = 'open'
        period.closing_balance = None
        period.closed_at = None
        period.closed_by = None
        period.notes = ''
        period.save(update_fields=['status', 'closing_balance', 'closed_at', 'closed_by', 'notes'])

        return period

    def archive_period(self, period_id):
        """
        Arquiva um período fechado.

        Args:
            period_id: ID do período a ser arquivado

        Returns:
            O período arquivado

        Raises:
            ValueError: Se o período não puder ser arquivado
        """
        try:
            period = AccountingPeriod.objects.get(id=period_id)
        except AccountingPeriod.DoesNotExist:
            raise ValueError('Período não encontrado.')

        if period.status != 'closed':
            raise ValueError('Apenas períodos fechados podem ser arquivados.')

        period.status = 'archived'
        period.save(update_fields=['status'])

        return period

    def get_current_balance(self):
        """
        Retorna o saldo atual do sistema.

        Cálculo:
        1. Soma dos closing_balance de todos os períodos fechados
        2. + Transações do período aberto mais recente

        Returns:
            O saldo atual
        """
        # Soma dos saldos de períodos fechados
        closed_periods = AccountingPeriod.objects.filter(
            status__in=['closed', 'archived'],
            closing_balance__isnull=False
        ).order_by('-month')

        balance = Decimal('0.00')

        # Pegar o último período fechado e usar seu closing_balance
        if closed_periods.exists():
            latest_closed = closed_periods.first()
            balance = latest_closed.closing_balance

        # Adicionar transações do período aberto
        open_period = AccountingPeriod.objects.filter(
            status='open'
        ).order_by('-month').first()

        if open_period:
            balance += self.calculate_period_transactions(open_period)

        return balance

    def get_balance_at_date(self, target_date):
        """
        Retorna o saldo em uma data específica.

        Nota: As transações negativas têm amount armazenado como valor negativo.

        Args:
            target_date: Data para cálculo do saldo

        Returns:
            O saldo na data especificada
        """
        if not isinstance(target_date, date):
            target_date = datetime.strptime(target_date, '%Y-%m-%d').date()

        # Encontrar o período da data
        period_month = target_date.replace(day=1)

        try:
            period = AccountingPeriod.objects.get(month=period_month)
        except AccountingPeriod.DoesNotExist:
            # Se não existe período, retornar 0
            return Decimal('0.00')

        # Se o período está fechado e a data é posterior ao fechamento,
        # usar o closing_balance
        if period.is_closed and period.closing_balance:
            return period.closing_balance

        # Caso contrário, calcular
        balance = period.opening_balance

        # Somar todas as transações até a data (já inclui sinais)
        transactions = TransactionModel.objects.filter(
            accounting_period=period,
            date__lte=target_date,
            transaction_type='original'
        )

        net = transactions.aggregate(
            total=Coalesce(Sum('amount'), Decimal('0.00'))
        )['total'] or Decimal('0.00')

        balance += net

        return balance

    def calculate_period_balance(self, period):
        """
        Calcula o saldo de um período.

        Cálculo: opening_balance + (entradas - saídas)

        Args:
            period: Instância de AccountingPeriod

        Returns:
            O saldo calculado
        """
        balance = period.opening_balance
        balance += self.calculate_period_transactions(period)
        return balance

    def calculate_period_transactions(self, period):
        """
        Calcula o valor líquido das transações de um período.

        Nota: As transações negativas têm amount armazenado como valor negativo,
        então somamos diretamente positivo + negativo.

        Args:
            period: Instância de AccountingPeriod

        Returns:
            O valor líquido (positivas + negativas, onde negativas já são negativas)
        """
        transactions = TransactionModel.objects.filter(
            accounting_period=period,
            transaction_type='original'
        )

        # Somar todas as transações diretamente (já inclui o sinal)
        net = transactions.aggregate(
            total=Coalesce(Sum('amount'), Decimal('0.00'), output_field=DecimalField())
        )['total'] or Decimal('0.00')

        return net

    def can_edit_transaction(self, transaction):
        """
        Verifica se uma transação pode ser editada.

        Args:
            transaction: Instância de TransactionModel

        Returns:
            True se a transação pode ser editada, False caso contrário
        """
        if not transaction.accounting_period:
            return True
        return transaction.accounting_period.is_open

    def can_delete_transaction(self, transaction):
        """
        Verifica se uma transação pode ser deletada.

        Args:
            transaction: Instância de TransactionModel

        Returns:
            True se a transação pode ser deletada, False caso contrário
        """
        return self.can_edit_transaction(transaction)

    def can_reverse_transaction(self, transaction):
        """
        Verifica se uma transação pode ser estornada.

        Args:
            transaction: Instância de TransactionModel

        Returns:
            True se a transação pode ser estornada, False caso contrário
        """
        if not transaction.accounting_period:
            return False
        if transaction.transaction_type == 'reversal':
            return False
        if transaction.has_reversal:
            return False
        return not transaction.accounting_period.is_open

    def get_or_create_period(self, date):
        """
        Obtém ou cria um período para uma data.

        Args:
            date: Data de referência

        Returns:
            Instância de AccountingPeriod
        """
        month = date.replace(day=1)

        period, created = AccountingPeriod.objects.get_or_create(
            month=month,
            defaults={'status': 'open', 'opening_balance': Decimal('0.00')}
        )

        if created:
            # Tentar herdar opening_balance do período anterior
            previous_period = period.get_previous_period()
            if previous_period and previous_period.closing_balance:
                period.opening_balance = previous_period.closing_balance
                period.save(update_fields=['opening_balance'])

        return period

    def verify_period_balance(self, period):
        """
        Verifica a consistência do saldo de um período fechado.

        Compara o closing_balance fixado com o saldo recalculado.

        Args:
            period: Instância de AccountingPeriod

        Returns:
            Dicionário com:
            - is_consistent: bool
            - fixed_balance: Decimal (saldo fixado)
            - calculated_balance: Decimal (saldo recalculado)
            - difference: Decimal (diferença, se houver)
        """
        if not period.is_closed or not period.closing_balance:
            return {
                'is_consistent': None,
                'message': 'Período não está fechado ou não tem closing_balance.',
            }

        calculated = self.calculate_period_balance(period)
        difference = period.closing_balance - calculated

        return {
            'is_consistent': difference == 0,
            'fixed_balance': period.closing_balance,
            'calculated_balance': calculated,
            'difference': difference,
        }

    def get_period_summary(self, period):
        """
        Retorna um resumo detalhado do período.

        Nota: As transações negativas têm amount armazenado como valor negativo.

        Args:
            period: Instância de AccountingPeriod

        Returns:
            Dicionário com informações do período
        """
        transactions = TransactionModel.objects.filter(
            accounting_period=period,
            transaction_type='original'
        )

        positive = transactions.filter(is_positive=True).aggregate(
            total=Coalesce(Sum('amount'), Decimal('0.00')),
            count=Count('id')
        )
        negative_abs = transactions.filter(is_positive=False).aggregate(
            total=Coalesce(Sum('amount'), Decimal('0.00')),
            count=Count('id')
        )

        # Net é a soma real (já inclui sinais)
        net = transactions.aggregate(
            total=Coalesce(Sum('amount'), Decimal('0.00'))
        )['total'] or Decimal('0.00')

        return {
            'period': period,
            'opening_balance': period.opening_balance,
            'closing_balance': period.closing_balance,
            'current_balance': self.calculate_period_balance(period),
            'total_positive': positive['total'] or Decimal('0.00'),
            'total_negative': abs(negative_abs['total'] or Decimal('0.00')),
            'net': net,
            'positive_count': positive['count'] or 0,
            'negative_count': negative_abs['count'] or 0,
            'total_transactions': transactions.count(),
        }

    def get_periods_with_balance(self, year=None):
        """
        Retorna períodos com informações de saldo.

        Args:
            year: Filtro opcional por ano

        Returns:
            QuerySet de AccountingPeriod com anotações de saldo
        """
        queryset = AccountingPeriod.objects.all()

        if year:
            queryset = queryset.filter(month__year=year)

        return queryset.order_by('-month')
