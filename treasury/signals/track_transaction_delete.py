from django.db.models.signals import pre_delete
from django.dispatch import receiver
from treasury.models import TransactionModel
import logging

logger = logging.getLogger(__name__)


@receiver(pre_delete, sender=TransactionModel)
def track_transaction_delete(sender, instance, **kwargs):
    from treasury.models import TransactionEditHistory

    if instance.pk:

        try:
            original_transaction = TransactionModel.objects.get(pk=instance.pk)
            TransactionEditHistory.objects.create(
                user=instance.user,
                transaction=instance,
                original_description=original_transaction.description,
                original_amount=original_transaction.amount,
                original_date=original_transaction.date,
                edited_description=instance.description,
                edited_amount=instance.amount,
                edited_date=instance.date,
            )
        except TransactionModel.DoesNotExist:
            logger.info("Pre_delete chamado, mas não há transaçao...")
