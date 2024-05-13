from django.db.models.signals import post_delete
from django.dispatch import receiver
from treasury.models import TransactionModel, MonthlyBalance
from django.db import transaction


@receiver(post_delete, sender=TransactionModel)
def update_monthly_balance_on_delete(sender, instance, **kwargs):
    transaction_month = instance.date.replace(day=1)
    first_month = MonthlyBalance.objects.get(is_first_month=True)
    if first_month.month <= instance.date.replace(day=1):
        month = instance.date.replace(day=1)
        amount = instance.amount
        with transaction.atomic():
            monthly_balance = MonthlyBalance.objects.get(month=month)
            monthly_balance.balance -= amount
            monthly_balance.save()
    else:
        pass
