from django.db.models.signals import post_save
from django.dispatch import receiver
from treasury.models import MonthlyBalance
from treasury.utils import check_and_create_missing_balances, all_balances_present
from datetime import datetime


@receiver(post_save, sender=MonthlyBalance)
def create_missing_monthly_balances(sender, instance, created, **kwargs):
    current_month = datetime.now().date().replace(day=1)

    if created and instance.is_first_month:
        if instance.month < current_month:
            post_save.disconnect(
                receiver=create_missing_monthly_balances,
                sender=MonthlyBalance,
            )
            check_and_create_missing_balances(instance.month)
            post_save.connect(
                receiver=create_missing_monthly_balances,
                sender=MonthlyBalance,
            )
        elif instance.month == current_month:
            pass
    else:
        if all_balances_present():
            pass
        else:
            post_save.disconnect(
                receiver=create_missing_monthly_balances,
                sender=MonthlyBalance,
            )
            check_and_create_missing_balances(instance.month)
            post_save.connect(
                receiver=create_missing_monthly_balances,
                sender=MonthlyBalance,
            )
