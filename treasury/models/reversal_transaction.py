from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone


class ReversalTransaction(models.Model):
    """
    Registra estornos de transações de períodos fechados.

    Quando uma transação de um período fechado precisa ser corrigida,
    não é possível editá-la diretamente. Ao invés disso, cria-se uma
    transação de estorno que registra a correção de forma auditável.

    O estorno cria duas transações:
    1. A transação original é marcada como estornada (via related name)
    2. Uma nova transação é criada com o valor corrigido

    Este modelo mantém o registro histórico dessa operação.
    """

    original_transaction = models.ForeignKey(
        'treasury.TransactionModel',
        on_delete=models.PROTECT,
        related_name='reversals',
        help_text="Transação original que está sendo estornada"
    )

    reversal_transaction = models.ForeignKey(
        'treasury.TransactionModel',
        on_delete=models.PROTECT,
        related_name='reversed_original',
        help_text="Nova transação que substitui a original"
    )

    reason = models.TextField(
        help_text="Motivo do estorno"
    )

    authorized_by = models.ForeignKey(
        'users.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='authorized_reversals',
        help_text="Usuário que autorizou o estorno (para períodos arquivados)"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        'users.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_reversals',
        help_text="Usuário que criou o estorno"
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'estorno de transação'
        verbose_name_plural = 'estornos de transações'
        indexes = [
            models.Index(fields=['original_transaction']),
            models.Index(fields=['reversal_transaction']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"Estorno de {self.original_transaction} criado em {self.created_at.strftime('%d/%m/%Y')}"

    def clean(self):
        """Validações antes de salvar."""
        super().clean()

        # Verificar que as transações são diferentes
        if self.original_transaction_id == self.reversal_transaction_id:
            raise ValidationError({
                'reversal_transaction': 'A transação de estorno deve ser diferente da original.'
            })

        # Verificar que a transação original é de um período fechado
        if self.original_transaction.accounting_period:
            if self.original_transaction.accounting_period.is_open:
                raise ValidationError({
                    'original_transaction': 'Transações de períodos abertos não precisam de estorno. Edite diretamente.'
                })

        # Verificar que a transação de estorno é do tipo correto
        if self.reversal_transaction.transaction_type != 'reversal':
            raise ValidationError({
                'reversal_transaction': 'A transação de estorno deve ter transaction_type="reversal".'
            })

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def original_amount(self):
        """Retorna o valor da transação original (com sinal)."""
        amount = self.original_transaction.amount
        return amount if self.original_transaction.is_positive else -amount

    @property
    def reversal_amount(self):
        """Retorna o valor da transação de estorno (com sinal)."""
        amount = self.reversal_transaction.amount
        return amount if self.reversal_transaction.is_positive else -amount

    @property
    def difference(self):
        """Retorna a diferença entre os valores (estorno - original)."""
        return self.reversal_amount - self.original_amount

    @classmethod
    def create_reversal(cls, original_transaction, new_data, reason, user, authorized_by=None):
        """
        Cria um estorno de transação de forma controlada.

        Args:
            original_transaction: A transação a ser estornada
            new_data: Dicionário com os novos dados (description, amount, is_positive, etc.)
            reason: Motivo do estorno
            user: Usuário que está criando o estorno
            authorized_by: Usuário que autorizou (obrigatório para períodos arquivados)

        Returns:
            A instância de ReversalTransaction criada
        """
        from treasury.models.transaction import TransactionModel

        # Validar período
        if not original_transaction.accounting_period:
            raise ValidationError('A transação original deve estar vinculada a um período contábil.')

        period = original_transaction.accounting_period

        if period.is_open:
            raise ValidationError('Transações de períodos abertos podem ser editadas diretamente.')

        if period.is_archived and not authorized_by:
            raise ValidationError('Estornos em períodos arquivados requerem autorização.')

        # Criar a transação de estorno
        reversal_transaction = TransactionModel.objects.create(
            user=user,
            category=new_data.get('category', original_transaction.category),
            description=f"ESTORNO: {new_data.get('description', original_transaction.description)}",
            amount=new_data.get('amount', original_transaction.amount),
            is_positive=new_data.get('is_positive', original_transaction.is_positive),
            date=timezone.now().date(),
            accounting_period=period,
            transaction_type='reversal',
            reverses=original_transaction,
            created_by=user,
        )

        # Copiar documento se fornecido
        if 'acquittance_doc' in new_data and new_data['acquittance_doc']:
            reversal_transaction.acquittance_doc = new_data['acquittance_doc']
            reversal_transaction.save()

        # Criar o registro de estorno
        reversal = cls.objects.create(
            original_transaction=original_transaction,
            reversal_transaction=reversal_transaction,
            reason=reason,
            created_by=user,
            authorized_by=authorized_by,
        )

        return reversal
