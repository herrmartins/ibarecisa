from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from django.contrib.auth import get_user_model
from django.db import models
from decimal import Decimal

from treasury.models import (
    AccountingPeriod,
    TransactionModel,
    ReversalTransaction,
    CategoryModel,
    AuditLog,
)

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Serializer básico para User."""

    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']


class CategorySerializer(serializers.ModelSerializer):
    """Serializer para CategoryModel."""

    class Meta:
        model = CategoryModel
        fields = ['id', 'name']
        read_only_fields = ['id']


class CategoryDetailSerializer(CategorySerializer):
    """Serializer detalhado para CategoryModel com estatísticas."""

    transaction_count = serializers.SerializerMethodField()
    total_amount = serializers.SerializerMethodField()

    class Meta(CategorySerializer.Meta):
        fields = CategorySerializer.Meta.fields + ['transaction_count', 'total_amount']

    def get_transaction_count(self, obj):
        return obj.transactions.count()

    def get_total_amount(self, obj):
        return obj.transactions.aggregate(
            total=serializers.FloatField(serializers.Sum('amount'))
        )['total'] or 0


class PeriodBalanceSerializer(serializers.Serializer):
    """Serializer para retornar o saldo de um período."""

    period_id = serializers.IntegerField()
    period_name = serializers.CharField()
    opening_balance = serializers.DecimalField(max_digits=10, decimal_places=2)
    current_balance = serializers.DecimalField(max_digits=10, decimal_places=2)
    closing_balance = serializers.DecimalField(max_digits=10, decimal_places=2, allow_null=True)
    status = serializers.CharField()
    is_open = serializers.BooleanField()


class AccountingPeriodSerializer(serializers.ModelSerializer):
    """Serializer para AccountingPeriod."""

    year = serializers.IntegerField(read_only=True)
    month_number = serializers.IntegerField(read_only=True, source='month.month')
    month_name = serializers.CharField(read_only=True)
    first_day = serializers.DateField(read_only=True)
    last_day = serializers.DateField(read_only=True)
    is_open = serializers.BooleanField(read_only=True)
    is_closed = serializers.BooleanField(read_only=True)
    is_archived = serializers.BooleanField(read_only=True)
    is_current_month = serializers.BooleanField(read_only=True)
    can_be_closed = serializers.BooleanField(read_only=True)
    closed_by_name = serializers.CharField(source='closed_by.get_full_name', read_only=True, allow_null=True)

    # Resumo de transações
    transactions_summary = serializers.SerializerMethodField()

    class Meta:
        model = AccountingPeriod
        fields = [
            'id',
            'month',
            'year',
            'month_number',
            'month_name',
            'first_day',
            'last_day',
            'status',
            'opening_balance',
            'closing_balance',
            'is_open',
            'is_closed',
            'is_archived',
            'is_current_month',
            'can_be_closed',
            'is_first_month',
            'closed_at',
            'closed_by',
            'closed_by_name',
            'notes',
            'transactions_summary',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'year',
            'month_number',
            'month_name',
            'first_day',
            'last_day',
            'is_open',
            'is_closed',
            'is_archived',
            'can_be_closed',
            'closed_at',
            'closed_by',
            'closed_by_name',
            'created_at',
            'updated_at',
        ]

    def get_transactions_summary(self, obj):
        summary = obj.get_transactions_summary()
        return {
            'total_positive': float(summary['total_positive']),
            'total_negative': float(summary['total_negative']),
            'net': float(summary['net']),
            'count': summary['count'],
        }

    def validate_month(self, value):
        """Valida que o mês é o primeiro dia."""
        if value.day != 1:
            raise serializers.ValidationError("A data deve ser o primeiro dia do mês.")
        return value


class AccountingPeriodCloseSerializer(serializers.Serializer):
    """Serializer para fechar um período contábil."""

    notes = serializers.CharField(required=False, allow_blank=True, max_length=1000)

    def validate(self, attrs):
        period = self.context['period']
        if not period.can_be_closed:
            if period.is_current_month:
                raise serializers.ValidationError(
                    f"O período {period.month_name}/{period.year} não pode ser fechado "
                    "porque é o mês corrente. Aguarde o mês terminar."
                )
            if period.status == 'closed':
                raise serializers.ValidationError("Este período já está fechado.")
            if period.status == 'archived':
                raise serializers.ValidationError("Este período está arquivado e não pode ser fechado novamente.")
            raise serializers.ValidationError("Apenas períodos abertos podem ser fechados.")
        return attrs


class AccountingPeriodSimpleSerializer(serializers.ModelSerializer):
    """Serializer simplificado para AccountingPeriod em transações."""

    month_name = serializers.CharField(read_only=True)
    year = serializers.IntegerField(read_only=True, source='month.year')
    opening_balance = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    closing_balance = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True, allow_null=True)
    transactions_summary = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = AccountingPeriod
        fields = ['id', 'month', 'month_name', 'year', 'status', 'opening_balance', 'closing_balance', 'transactions_summary']

    def get_transactions_summary(self, obj):
        """Retorna o resumo das transações do período."""
        from treasury.models.transaction import TransactionModel

        transactions = TransactionModel.objects.filter(
            accounting_period=obj,
            transaction_type='original'
        )

        positive = transactions.filter(is_positive=True).aggregate(
            total=models.Sum('amount')
        )['total'] or 0

        negative = transactions.filter(is_positive=False).aggregate(
            total=models.Sum('amount')
        )['total'] or 0

        # Net = positivas + negativas (negative já é negativo)
        net = positive + negative

        return {
            'total_positive': positive,
            'total_negative': negative,
            'net': net,
            'count': transactions.count(),
            'positive_count': transactions.filter(is_positive=True).count(),
            'negative_count': transactions.filter(is_positive=False).count(),
        }


class TransactionSerializer(serializers.ModelSerializer):
    """Serializer para TransactionModel (leitura)."""

    signed_amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    can_be_edited = serializers.BooleanField(read_only=True)
    can_be_deleted = serializers.BooleanField(read_only=True)
    can_be_reversed = serializers.BooleanField(read_only=True)
    has_reversal = serializers.BooleanField(read_only=True)

    # Informações relacionadas
    category = CategorySerializer(read_only=True, allow_null=True)
    category_name = serializers.CharField(source='category.name', read_only=True, allow_null=True)
    accounting_period = AccountingPeriodSerializer(read_only=True, allow_null=True)
    period_name = serializers.CharField(source='accounting_period.month_name', read_only=True, allow_null=True)
    period_status = serializers.CharField(source='accounting_period.status', read_only=True, allow_null=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    created_by = UserSerializer(read_only=True, allow_null=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True, allow_null=True)
    reversal_count = serializers.SerializerMethodField()

    class Meta:
        model = TransactionModel
        fields = [
            'id',
            'user',
            'user_name',
            'category',
            'category_name',
            'description',
            'amount',
            'is_positive',
            'signed_amount',
            'date',
            'acquittance_doc',
            'accounting_period',
            'period_name',
            'period_status',
            'transaction_type',
            'reverses',
            'created_by',
            'created_by_name',
            'created_at',
            'updated_at',
            'can_be_edited',
            'can_be_deleted',
            'can_be_reversed',
            'has_reversal',
            'reversal_count',
        ]
        read_only_fields = [
            'id',
            'signed_amount',
            'can_be_edited',
            'can_be_deleted',
            'can_be_reversed',
            'has_reversal',
            'user_name',
            'category_name',
            'period_name',
            'period_status',
            'created_by_name',
            'created_at',
            'updated_at',
            'reversal_count',
        ]

    def get_reversal_count(self, obj):
        return obj.reversals.count()


class TransactionListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listagem de transações."""

    signed_amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    category = CategorySerializer(read_only=True, allow_null=True)
    category_name = serializers.CharField(source='category.name', read_only=True, allow_null=True)
    accounting_period = AccountingPeriodSerializer(read_only=True, allow_null=True)
    period_name = serializers.SerializerMethodField()
    period_status = serializers.CharField(source='accounting_period.status', read_only=True, allow_null=True)
    can_be_edited = serializers.BooleanField(read_only=True)

    class Meta:
        model = TransactionModel
        fields = [
            'id',
            'description',
            'amount',
            'is_positive',
            'signed_amount',
            'date',
            'category',
            'category_name',
            'accounting_period',
            'period_name',
            'period_status',
            'transaction_type',
            'can_be_edited',
        ]

    def get_period_name(self, obj):
        if obj.accounting_period:
            return obj.accounting_period.month_name
        return None


class TransactionCreateSerializer(serializers.ModelSerializer):
    """Serializer para criar transações."""

    class Meta:
        model = TransactionModel
        fields = [
            'category',
            'description',
            'amount',
            'is_positive',
            'date',
            'acquittance_doc',
        ]

    def validate_date(self, value):
        """Valida que a data não é futura."""
        from django.utils import timezone
        today = timezone.now().date()
        if value > today:
            raise serializers.ValidationError("Não é permitido criar transações com data futura.")
        return value

    def validate_amount(self, value):
        """Valida que o amount é positivo."""
        if value <= 0:
            raise serializers.ValidationError("O valor deve ser positivo.")
        return value

    def create(self, validated_data):
        """Cria a transação vinculando ao usuário e período."""
        request = self.context['request']
        user = request.user

        # Encontrar ou criar o período
        from treasury.models import AccountingPeriod
        period_month = validated_data['date'].replace(day=1)

        # Se o período ainda não existe, calcular o opening_balance correto
        if not AccountingPeriod.objects.filter(month=period_month).exists():
            # Buscar período anterior
            if period_month.month == 1:
                prev_month = period_month.replace(year=period_month.year - 1, month=12, day=1)
            else:
                prev_month = period_month.replace(month=period_month.month - 1, day=1)

            opening_balance = Decimal('0.00')
            try:
                prev_period = AccountingPeriod.objects.get(month=prev_month)
                # Usar closing_balance se existir (período fechado)
                if prev_period.closing_balance is not None:
                    opening_balance = prev_period.closing_balance
                else:
                    # Período anterior aberto - usar saldo atual
                    opening_balance = prev_period.get_current_balance()
            except AccountingPeriod.DoesNotExist:
                # Sem período anterior, abre com 0
                opening_balance = Decimal('0.00')

            period = AccountingPeriod.objects.create(
                month=period_month,
                status='open',
                opening_balance=opening_balance
            )
        else:
            period = AccountingPeriod.objects.get(month=period_month)

        # Verificar se o período está fechado
        if period.is_closed:
            raise serializers.ValidationError(
                f"Não é possível criar transações no período {period.month_name}/{period.year} "
                "porque ele está fechado. Reabra o período primeiro ou utilize a funcionalidade de estorno."
            )

        # Criar a transação
        transaction = TransactionModel.objects.create(
            user=user,
            created_by=user,
            accounting_period=period,
            **validated_data
        )

        # Log de auditoria
        AuditLog.log(
            action='transaction_created',
            entity_type='TransactionModel',
            entity_id=transaction.id,
            user=user,
            old_values=None,
            new_values={
                'description': transaction.description,
                'amount': float(transaction.amount),
                'is_positive': transaction.is_positive,
                'date': str(transaction.date),
                'category_id': transaction.category_id,
            },
            description=f'Transação criada: {transaction.description}',
            period_id=period.id,
            request=request,
        )

        return transaction


class TransactionUpdateSerializer(serializers.ModelSerializer):
    """Serializer para atualizar transações."""

    class Meta:
        model = TransactionModel
        fields = [
            'category',
            'description',
            'amount',
            'is_positive',
            'date',
            'acquittance_doc',
        ]

    def validate_date(self, value):
        """Valida que a data não é futura."""
        from django.utils import timezone
        today = timezone.now().date()
        if value > today:
            raise serializers.ValidationError("Não é permitido criar transações com data futura.")
        return value

    def validate_amount(self, value):
        """Valida que o amount é positivo."""
        if value <= 0:
            raise serializers.ValidationError("O valor deve ser positivo.")
        return value

    def update(self, instance, validated_data):
        """Atualiza a transação com validação de período."""
        # Verificar se o período está fechado
        if instance.accounting_period and instance.accounting_period.is_closed:
            raise serializers.ValidationError(
                "Não é possível editar transações de períodos fechados. "
                "Utilize a funcionalidade de estorno."
            )

        request = self.context['request']
        user = request.user

        # Salvar valores antigos para auditoria
        old_values = {
            'description': instance.description,
            'amount': float(instance.amount),
            'is_positive': instance.is_positive,
            'date': str(instance.date),
            'category_id': instance.category_id,
        }

        # Atualizar os campos
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()

        # Log de auditoria
        period_id = instance.accounting_period.id if instance.accounting_period else None
        AuditLog.log(
            action='transaction_updated',
            entity_type='TransactionModel',
            entity_id=instance.id,
            user=user,
            old_values=old_values,
            new_values={
                'description': instance.description,
                'amount': float(instance.amount),
                'is_positive': instance.is_positive,
                'date': str(instance.date),
                'category_id': instance.category_id,
            },
            description=f'Transação atualizada: {instance.description}',
            period_id=period_id,
            request=request,
        )

        return instance


class ReversalTransactionSerializer(serializers.ModelSerializer):
    """Serializer para ReversalTransaction."""

    original_amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    reversal_amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    difference = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    created_by = UserSerializer(read_only=True, allow_null=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True, allow_null=True)
    authorized_by = UserSerializer(read_only=True, allow_null=True)
    authorized_by_name = serializers.CharField(source='authorized_by.get_full_name', read_only=True, allow_null=True)

    # Informações das transações
    original_transaction = TransactionListSerializer(read_only=True)
    reversal_transaction = TransactionListSerializer(read_only=True)

    class Meta:
        model = ReversalTransaction
        fields = [
            'id',
            'original_transaction',
            'reversal_transaction',
            'reason',
            'original_amount',
            'reversal_amount',
            'difference',
            'authorized_by',
            'authorized_by_name',
            'created_by',
            'created_by_name',
            'created_at',
        ]
        read_only_fields = [
            'id',
            'original_amount',
            'reversal_amount',
            'difference',
            'created_by',
            'created_at',
        ]


class ReversalCreateSerializer(serializers.Serializer):
    """Serializer para criar um estorno."""

    original_transaction_id = serializers.IntegerField(write_only=True)
    description = serializers.CharField(max_length=255, required=False)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    is_positive = serializers.BooleanField()
    category_id = serializers.IntegerField(required=False, allow_null=True)
    reason = serializers.CharField(max_length=1000)
    authorized_by_id = serializers.IntegerField(required=False, allow_null=True)
    acquittance_doc = serializers.ImageField(required=False, allow_null=True)

    def validate_original_transaction_id(self, value):
        """Valida que a transação original existe."""
        try:
            transaction = TransactionModel.objects.get(id=value)
            if not transaction.can_be_reversed:
                raise serializers.ValidationError(
                    "Esta transação não pode ser estornada. "
                    "Verifique se ela pertence a um período fechado."
                )
            if transaction.has_reversal:
                raise serializers.ValidationError("Esta transação já possui um estorno.")
            return value
        except TransactionModel.DoesNotExist:
            raise serializers.ValidationError("Transação não encontrada.")

    def validate(self, attrs):
        """Validações adicionais."""
        # Se o período está arquivado, exige autorização
        transaction = TransactionModel.objects.get(id=attrs['original_transaction_id'])
        if transaction.accounting_period.is_archived:
            if not attrs.get('authorized_by_id'):
                raise serializers.ValidationError(
                    "Estornos em períodos arquivados requerem autorização de um administrador."
                )
        return attrs

    def create(self, validated_data):
        """Cria o estorno."""
        request = self.context['request']
        user = request.user

        original_transaction = TransactionModel.objects.get(
            id=validated_data['original_transaction_id']
        )

        # Preparar dados da nova transação
        new_data = {
            'description': validated_data.get('description', original_transaction.description),
            'amount': validated_data['amount'],
            'is_positive': validated_data['is_positive'],
            'category_id': validated_data.get('category_id'),
            'acquittance_doc': validated_data.get('acquittance_doc'),
        }

        if new_data['category_id']:
            try:
                new_data['category'] = CategoryModel.objects.get(id=new_data.pop('category_id'))
            except CategoryModel.DoesNotExist:
                pass

        # Salvar valores antigos para auditoria
        old_values = {
            'original_transaction_id': original_transaction.id,
            'original_description': original_transaction.description,
            'original_amount': float(original_transaction.amount),
            'original_is_positive': original_transaction.is_positive,
        }

        # Criar o estorno
        reversal = ReversalTransaction.create_reversal(
            original_transaction=original_transaction,
            new_data=new_data,
            reason=validated_data['reason'],
            user=user,
            authorized_by_id=validated_data.get('authorized_by_id'),
        )

        # Log de auditoria
        period_id = original_transaction.accounting_period.id if original_transaction.accounting_period else None
        AuditLog.log(
            action='transaction_reversed',
            entity_type='TransactionModel',
            entity_id=original_transaction.id,
            user=user,
            old_values=old_values,
            new_values={
                'reversal_description': new_data.get('description'),
                'reversal_amount': float(new_data['amount']),
                'reversal_is_positive': new_data['is_positive'],
                'reason': validated_data['reason'],
                'reversal_transaction_id': reversal.reversal_transaction.id,
            },
            description=f'Estorno criado: {validated_data["reason"]}',
            period_id=period_id,
            request=request,
        )

        return reversal


# Exportar todos os serializers
__all__ = [
    'CategorySerializer',
    'CategoryDetailSerializer',
    'PeriodBalanceSerializer',
    'AccountingPeriodSerializer',
    'AccountingPeriodSimpleSerializer',
    'AccountingPeriodCloseSerializer',
    'TransactionSerializer',
    'TransactionListSerializer',
    'TransactionCreateSerializer',
    'TransactionUpdateSerializer',
    'ReversalTransactionSerializer',
    'ReversalCreateSerializer',
]
