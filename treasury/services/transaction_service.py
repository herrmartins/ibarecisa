from django.db.models import Sum, Q, Count
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.core.exceptions import ValidationError
from decimal import Decimal

from treasury.models import TransactionModel, ReversalTransaction, AccountingPeriod, CategoryModel


class TransactionService:
    """
    Serviço para lógica de negócio relacionada a transações.

    Responsável por:
    - Criação de transações
    - Criação de estornos
    - Cálculos de transações por período
    - Validações
    """

    def create_transaction(self, data, user):
        """
        Cria uma nova transação vinculando ao período contábil.

        Args:
            data: Dicionário com os dados da transação
            user: Usuário que está criando a transação

        Returns:
            A transação criada

        Raises:
            ValidationError: Se os dados forem inválidos
        """
        from treasury.services.period_service import PeriodService

        # Validar data futura
        if data['date'] > timezone.now().date():
            raise ValidationError("Não é permitido criar transações com data futura.")

        # Validar amount positivo
        if data['amount'] <= 0:
            raise ValidationError("O valor deve ser positivo.")

        # Obter ou criar o período
        period_service = PeriodService()
        period = period_service.get_or_create_period(data['date'])

        # Criar a transação
        transaction = TransactionModel.objects.create(
            user=user,
            created_by=user,
            accounting_period=period,
            description=data.get('description', ''),
            amount=data['amount'],
            is_positive=data.get('is_positive', True),
            date=data['date'],
            category=data.get('category'),
            acquittance_doc=data.get('acquittance_doc'),
            transaction_type='original',
        )

        return transaction

    def update_transaction(self, transaction, data, user):
        """
        Atualiza uma transação existente.

        Args:
            transaction: Instância de TransactionModel
            data: Dicionário com os novos dados
            user: Usuário que está editando

        Returns:
            A transação atualizada

        Raises:
            ValidationError: Se a transação não puder ser editada
        """
        from treasury.services.period_service import PeriodService

        period_service = PeriodService()

        # Verificar se pode editar
        if not period_service.can_edit_transaction(transaction):
            raise ValidationError(
                "Não é possível editar transações de períodos fechados. "
                "Utilize a funcionalidade de estorno."
            )

        # Validar data futura
        if 'date' in data and data['date'] > timezone.now().date():
            raise ValidationError("Não é permitido criar transações com data futura.")

        # Validar amount positivo
        if 'amount' in data and data['amount'] <= 0:
            raise ValidationError("O valor deve ser positivo.")

        # Atualizar campos
        for field, value in data.items():
            if field == 'category' and value is None:
                setattr(transaction, field, None)
            elif hasattr(transaction, field):
                setattr(transaction, field, value)

        # Se mudou a data, atualizar o período
        if 'date' in data:
            new_period = period_service.get_or_create_period(data['date'])
            transaction.accounting_period = new_period

        transaction.save()

        return transaction

    def delete_transaction(self, transaction):
        """
        Deleta uma transação.

        Args:
            transaction: Instância de TransactionModel

        Raises:
            ValidationError: Se a transação não puder ser deletada
        """
        from treasury.services.period_service import PeriodService

        period_service = PeriodService()

        # Verificar se pode deletar
        if not period_service.can_delete_transaction(transaction):
            raise ValidationError(
                "Não é possível deletar transações de períodos fechados."
            )

        transaction.delete()

    def create_reversal(self, original_transaction_id, new_data, reason, user, authorized_by=None):
        """
        Cria um estorno de transação.

        Processo:
        1. Valida a transação original
        2. Cria a transação de estorno
        3. Registra o estorno

        Args:
            original_transaction_id: ID da transação original
            new_data: Dicionário com os novos dados
            reason: Motivo do estorno
            user: Usuário que está criando o estorno
            authorized_by: Usuário que autorizou (obrigatório para períodos arquivados)

        Returns:
            A instância de ReversalTransaction criada

        Raises:
            ValidationError: Se o estorno não puder ser criado
        """
        from treasury.services.period_service import PeriodService

        # Buscar transação original
        try:
            original_transaction = TransactionModel.objects.get(id=original_transaction_id)
        except TransactionModel.DoesNotExist:
            raise ValidationError("Transação original não encontrada.")

        period_service = PeriodService()

        # Validar que pode ser estornada
        if not period_service.can_reverse_transaction(original_transaction):
            raise ValidationError("Esta transação não pode ser estornada.")

        # Validar período arquivado
        if original_transaction.accounting_period.is_archived and not authorized_by:
            raise ValidationError("Estornos em períodos arquivados requerem autorização.")

        # Validar amount positivo
        if new_data.get('amount', 0) <= 0:
            raise ValidationError("O valor deve ser positivo.")

        # Criar a transação de estorno
        reversal_transaction = TransactionModel.objects.create(
            user=user,
            created_by=user,
            accounting_period=original_transaction.accounting_period,
            category=new_data.get('category', original_transaction.category),
            description=new_data.get('description', f"ESTORNO: {original_transaction.description}"),
            amount=new_data.get('amount', original_transaction.amount),
            is_positive=new_data.get('is_positive', original_transaction.is_positive),
            date=timezone.now().date(),
            acquittance_doc=new_data.get('acquittance_doc'),
            transaction_type='reversal',
            reverses=original_transaction,
        )

        # Criar o registro de estorno
        reversal = ReversalTransaction.objects.create(
            original_transaction=original_transaction,
            reversal_transaction=reversal_transaction,
            reason=reason,
            created_by=user,
            authorized_by=authorized_by,
        )

        return reversal

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

        Considera apenas transações originais (não estornos).
        NOTA: Transações negativas já são armazenadas com amount negativo,
        então somamos diretamente.

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
            total=Coalesce(Sum('amount'), Decimal('0.00'))
        )['total'] or Decimal('0.00')

        return net

    def get_transactions_summary(self, period):
        """
        Retorna um resumo das transações de um período.

        Args:
            period: Instância de AccountingPeriod

        Returns:
            Dicionário com totais
        """
        transactions = TransactionModel.objects.filter(
            accounting_period=period,
            transaction_type='original'
        )

        positive = transactions.filter(is_positive=True).aggregate(
            total=Coalesce(Sum('amount'), Decimal('0.00')),
            count=Count('id')
        )
        negative = transactions.filter(is_positive=False).aggregate(
            total=Coalesce(Sum('amount'), Decimal('0.00')),
            count=Count('id')
        )

        return {
            'total_positive': positive['total'] or Decimal('0.00'),
            'total_negative': negative['total'] or Decimal('0.00'),
            'net': (positive['total'] or Decimal('0.00')) - (negative['total'] or Decimal('0.00')),
            'positive_count': positive['count'] or 0,
            'negative_count': negative['count'] or 0,
            'total_count': transactions.count(),
        }

    def get_transactions_by_category(self, period):
        """
        Retorna transações agrupadas por categoria.

        Args:
            period: Instância de AccountingPeriod

        Returns:
            Lista de dicionários com dados por categoria
        """
        transactions = TransactionModel.objects.filter(
            accounting_period=period,
            transaction_type='original'
        ).select_related('category')

        categories = {}

        for transaction in transactions:
            cat_name = transaction.category.name if transaction.category else 'Sem categoria'
            if cat_name not in categories:
                categories[cat_name] = {
                    'category': transaction.category,
                    'name': cat_name,
                    'positive': Decimal('0.00'),
                    'negative': Decimal('0.00'),
                    'count': 0,
                }

            if transaction.is_positive:
                categories[cat_name]['positive'] += transaction.amount
            else:
                categories[cat_name]['negative'] += transaction.amount
            categories[cat_name]['count'] += 1

        return list(categories.values())

    def validate_transaction_data(self, data):
        """
        Valida dados de transação antes de criar/atualizar.

        Args:
            data: Dicionário com os dados da transação

        Returns:
            Tupla (is_valid, errors)

        Raises:
            ValidationError: Se os dados forem inválidos
        """
        errors = {}

        # Validar description
        if not data.get('description'):
            errors['description'] = 'A descrição é obrigatória.'

        # Validar amount
        amount = data.get('amount')
        if not amount:
            errors['amount'] = 'O valor é obrigatório.'
        elif amount <= 0:
            errors['amount'] = 'O valor deve ser positivo.'

        # Validar date
        if not data.get('date'):
            errors['date'] = 'A data é obrigatória.'
        elif data['date'] > timezone.now().date():
            errors['date'] = 'Não é permitido criar transações com data futura.'

        if errors:
            raise ValidationError(errors)

        return True, {}
