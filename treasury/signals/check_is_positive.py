from django.db.models.signals import pre_save
from django.dispatch import receiver
from treasury.models import TransactionModel


@receiver(pre_save, sender=TransactionModel)
def check_is_positive(sender, instance, **kwargs):
    if instance.amount < 0:
        instance.is_positive = False
    else:
        instance.is_positive = True
