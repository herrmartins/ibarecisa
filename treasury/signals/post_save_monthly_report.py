from django.db.models.signals import post_save
from django.dispatch import receiver
from treasury.models import MonthlyReportModel, MonthlyTransactionByCategoryModel
from treasury.utils import get_aggregate_transactions_by_category
from dateutil.relativedelta import relativedelta


def save_transactions(transactions_dict, instance, is_positive):
    for category, total_amount in transactions_dict.items():
        MonthlyTransactionByCategoryModel.objects.create(
            report=instance,
            category=category,
            total_amount=total_amount,
            is_positive=is_positive,
        )


@receiver(post_save, sender=MonthlyReportModel)
def post_save_monthly_report(sender, instance, created, **kwargs):
    if created:  # Runs only when a new instance is created
        year = instance.month.year
        month = instance.month.month
        report_month = instance.month

        report_month += relativedelta(months=+1)

        positive_transactions_dict = get_aggregate_transactions_by_category(
            year, month, True
        )
        negative_transactions_dict = get_aggregate_transactions_by_category(
            year, month, False
        )

        save_transactions(positive_transactions_dict, instance, is_positive=True)
        save_transactions(negative_transactions_dict, instance, is_positive=False)
