from django.db.models.signals import pre_save
from django.dispatch import receiver
from treasury.models import TransactionModel, MonthlyBalance
from django.db.models import Sum
from decimal import Decimal
from treasury.utils import (
    monthly_balance_exists,
    check_and_create_missing_balances,
    update_subsequent_balances,
)
from django.db import transaction
from datetime import datetime


@receiver(pre_save, sender=TransactionModel)
def update_monthly_balance_on_edit(sender, instance, **kwargs):
    if instance.pk:
        current_month = datetime.now().replace(day=1)
        transaction_month = instance.date.replace(day=1)
        first_month = MonthlyBalance.objects.get(is_first_month=True)
        old_instance = TransactionModel.objects.get(pk=instance.pk)
        old_amount = Decimal(old_instance.amount)
        new_amount = Decimal(instance.amount)
        difference = new_amount - old_amount

        if first_month.month <= instance.date.replace(day=1):

            if monthly_balance_exists(transaction_month):
                with transaction.atomic():
                    monthly_balance = MonthlyBalance.objects.get(
                        month=transaction_month)
                    monthly_balance.balance += difference
                    monthly_balance.save()

            else:
                #TESTAR URGENTE
                check_and_create_missing_balances(transaction_month)
                update_subsequent_balances(instance.date, instance.amount)
                instance.save()
        else:
            pass
