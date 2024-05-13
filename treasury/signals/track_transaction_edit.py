from django.db.models.signals import pre_save
from django.dispatch import receiver
from treasury.models import TransactionModel


@receiver(pre_save, sender=TransactionModel)
def track_transaction_edit(sender, instance, **kwargs):
    if instance.pk:
        from treasury.models import TransactionEditHistory

        try:
            original_transaction = TransactionModel.objects.get(pk=instance.pk)
            if (
                original_transaction.description != instance.description
                or original_transaction.amount != instance.amount
                or original_transaction.date != instance.date
            ):
                track_transaction = TransactionEditHistory.objects.create(
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
            print("No transactions found...")
