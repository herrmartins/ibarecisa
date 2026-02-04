"""
Signal para definir automaticamente o opening_balance quando um AccountingPeriod é criado.

O opening_balance deve ser o closing_balance do período anterior,
ou o saldo atual se o período anterior ainda estiver aberto.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from treasury.models import AccountingPeriod
from decimal import Decimal


@receiver(post_save, sender=AccountingPeriod)
def set_opening_balance_on_create(sender, instance, created, **kwargs):
    """
    Define automaticamente o opening_balance quando um novo AccountingPeriod é criado.

    O opening_balance deve ser o closing_balance do período anterior,
    ou o saldo atual se o período anterior ainda estiver aberto.
    """
    if not created:
        return  # Apenas executa na criação, não em atualizações

    # Pular se opening_balance já estiver definido (diferente de zero)
    if instance.opening_balance != Decimal('0.00'):
        return

    # Obter o período anterior
    prev_period = instance.get_previous_period()

    if prev_period:
        # Usar closing_balance se o período estiver fechado
        if prev_period.closing_balance is not None:
            instance.opening_balance = prev_period.closing_balance
        else:
            # Período está aberto - usar saldo atual
            instance.opening_balance = prev_period.get_current_balance()

        # Salvar sem disparar o sinal novamente
        AccountingPeriod.objects.filter(pk=instance.pk).update(
            opening_balance=instance.opening_balance
        )