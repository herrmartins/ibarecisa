from django.db.models.base import pre_save
from django.dispatch import receiver
from treasury.utils.update_subsequent_balances import update_subsequent_balances
from treasury.models import MonthlyBalance
from django.db import transaction
from decimal import Decimal


@receiver(pre_save, sender=MonthlyBalance)
def updated_subsequent_monthly_balances(sender, instance, **kwargs):
    if instance.pk:
        previous_balance = MonthlyBalance.objects.get(pk=instance.pk)
        previous_balance = Decimal(previous_balance.balance)
        difference = instance.balance - previous_balance

        pre_save.disconnect(
            receiver=updated_subsequent_monthly_balances,
            sender=MonthlyBalance,
        )
        with transaction.atomic():
            update_subsequent_balances(instance.month, difference)
            instance.save()
        pre_save.connect(
            receiver=updated_subsequent_monthly_balances,
            sender=MonthlyBalance,
        )
