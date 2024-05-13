from django.db.models.signals import post_save, pre_save, pre_delete
from django.dispatch import receiver
from treasury.models import (
    MonthlyReportModel,
    MonthlyTransactionByCategoryModel,
    MonthlyBalance,
    TransactionModel,
)
from .utils import get_aggregate_transactions_by_category
from dateutil.relativedelta import relativedelta
from django.utils import timezone
from django.db import models
from django.db.models import F, Sum
from decimal import Decimal


@receiver(post_save, sender=MonthlyReportModel)
def post_save_monthly_report(sender, instance, created, **kwargs):
    if created:
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

        save_transactions(positive_transactions_dict,
                          instance, is_positive=True)
        save_transactions(negative_transactions_dict,
                          instance, is_positive=False)


def save_transactions(transactions_dict, instance, is_positive):
    for category, total_amount in transactions_dict.items():
        MonthlyTransactionByCategoryModel.objects.create(
            report=instance,
            category=category,
            total_amount=total_amount,
            is_positive=is_positive,
        )


@receiver(post_save, sender=MonthlyBalance)
def create_missing_monthly_balances(sender, instance, created, **kwargs):
    if created:
        previous_month = instance.month - relativedelta(months=1)
        # Get the month the user saved
        instance_month = instance.month
        # Get the current date
        current_date = timezone.now().date()  # Extract date only
        n_while = 0
        while instance_month.year < current_date.year or (
            instance_month.year == current_date.year
            and instance_month.month <= current_date.month
        ):
            n_while += 1
            if not MonthlyBalance.objects.filter(month=instance_month).exists():
                is_first = instance_month == instance.month
                MonthlyBalance.objects.create(
                    month=instance_month,
                    is_first_month=is_first,
                    balance=instance.balance,
                )
            next_month = instance_month + relativedelta(months=1)
            instance_month = next_month.replace(day=1)


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


@receiver(pre_delete, sender=TransactionModel)
def update_monthly_balance_on_delete(sender, instance, **kwargs):
    month = instance.date.replace(day=1)
    amount = instance.amount

    new_monthly_balance = MonthlyBalance.objects.update_or_create(
        month=month, defaults={"balance": models.F("balance") - amount}
    )

    subsequent_months = MonthlyBalance.objects.filter(month__gt=month)
    for sub_month in subsequent_months:
        sub_month_transactions = TransactionModel.objects.filter(
            date__year=sub_month.month.year,
            date__month=sub_month.month.month,
        )
        sub_month_balance = (
            sub_month_transactions.aggregate(total_amount=Sum("amount"))[
                "total_amount"]
            or 0
        )

        sub_month.balance = sub_month_balance + (sub_month.balance - amount)
        sub_month.save()


@receiver(post_save, sender=TransactionModel)
def update_monthly_balance_on_create(sender, instance, created, **kwargs):
    if created:
        month = instance.date.replace(day=1)
        difference = instance.amount
        try:
            current_monthly_balance = MonthlyBalance.objects.get(month=month)
            current_monthly_balance.balance = F("balance") + difference
            current_monthly_balance.save()
        except MonthlyBalance.DoesNotExist:
            previous_month = month - relativedelta(months=1)
            try:
                previous_month_balance = MonthlyBalance.objects.get(
                    month=previous_month
                )
                previous_balance = previous_month_balance.balance
            except MonthlyBalance.DoesNotExist:
                previous_balance = 0

            MonthlyBalance.objects.create(
                month=month, balance=previous_balance + difference
            )

        subsequent_months = MonthlyBalance.objects.filter(month__gt=month)

        for sub_month in subsequent_months:
            sub_month_transactions = TransactionModel.objects.filter(
                date__year=sub_month.month.year,
                date__month=sub_month.month.month,
            )

            sub_month_balance = (
                sub_month_transactions.aggregate(total_amount=Sum("amount"))[
                    "total_amount"
                ]
                or 0
            )

            sub_month.balance = sub_month_balance + sub_month.balance - difference
            sub_month.save()


@receiver(pre_save, sender=TransactionModel)
def update_monthly_balance_on_edit(sender, instance, **kwargs):
    if instance.pk:
        old_instance = TransactionModel.objects.get(pk=instance.pk)
        old_amount = Decimal(old_instance.amount)
        new_amount = Decimal(instance.amount)

        if old_amount != new_amount:
            month = instance.date.replace(day=1)
            difference = new_amount - old_amount

            from treasury.models import MonthlyBalance

            # Update the current month's balance
            try:
                monthly_balance = MonthlyBalance.objects.get(month=month)
                monthly_balance.balance += difference
                monthly_balance.save()
            except MonthlyBalance.DoesNotExist:
                pass  # Handle the case if MonthlyBalance doesn't exist for the month

            # Update subsequent months' balances
            subsequent_months = MonthlyBalance.objects.filter(month__gt=month)
            prev_balance = difference  # Adjust balance based on the difference

            for sub_month in subsequent_months:
                sub_month_transactions = TransactionModel.objects.filter(
                    date__year=sub_month.month.year,
                    date__month=sub_month.month.month,
                )

                sub_month_balance = (
                    sub_month_transactions.aggregate(total_amount=Sum("amount"))[
                        "total_amount"
                    ]
                    or 0
                )

                sub_month.balance = sub_month_balance + prev_balance
                sub_month.save()
                prev_balance = sub_month.balance
