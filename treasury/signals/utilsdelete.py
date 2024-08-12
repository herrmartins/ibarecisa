from dateutil.relativedelta import relativedelta
from django.db.models import Sum
from dateutil.rrule import rrule, MONTHLY
from treasury.models import TransactionModel, MonthlyBalance
from django.utils import timezone
from django.db.models.signals import post_save, pre_save, pre_delete
from treasury.signals.create_missing_monthly_balances import (
    create_missing_monthly_balances,
)
from treasury.exceptions import NoInitialMonthlyBalance


def get_month_balance(month):
    previous_month = month
    try:
        balance = MonthlyBalance.objects.get(month=previous_month).balance
    except MonthlyBalance.DoesNotExist:
        return 0
    return balance


def months_between_dates(start_date, end_date):
    end_date = end_date + relativedelta(days=1)
    months = rrule(MONTHLY, dtstart=start_date, until=end_date)
    return months.count() - 1 if months else 0


def get_total_amount_transactions_by_month(month):
    month_transactions = TransactionModel.objects.filter(
        date__year=month.year,
        date__month=month.month,
    )

    month_transactions = (
        month_transactions.aggregate(total_amount=Sum("amount"))[
            "total_amount"] or 0
    )
    return month_transactions


def get_total_amount_transactions(transactions):
    transactions_amount = (
        transactions.aggregate(total_amount=Sum("amount"))["total_amount"] or 0
    )
    return transactions_amount


def add_months(start_date, months):
    return start_date + relativedelta(months=months)


def confirming_all_balances_present():
    current_month = timezone.now().date().replace(day=1)
    first_monthly_balance = MonthlyBalance.objects.filter(
        is_first_month=True).first()
    if not first_monthly_balance:
        raise NoInitialMonthlyBalance("You must create the initial balance...")

    months_diff = months_between_dates(
        first_monthly_balance.month, current_month)

    monthly_balances = MonthlyBalance.objects.filter(
        month__range=(first_monthly_balance.month, current_month)
    ).order_by("month")
    if monthly_balances.count() == months_diff + 1:
        return True
    else:
        return False


def check_monthly_balances_integrity(check_date, amount=None):
    current_month = timezone.now().date().replace(day=1)

    post_save.disconnect(
        receiver=create_missing_monthly_balances, sender=MonthlyBalance
    )

    first_monthly_balance = MonthlyBalance.objects.filter(
        is_first_month=True).first()
    if not first_monthly_balance:
        raise NoInitialMonthlyBalance("You must create the initial balance...")

    months_diff = months_between_dates(
        first_monthly_balance.month, current_month)

    monthly_balances = MonthlyBalance.objects.filter(
        month__range=(first_monthly_balance.month, current_month)
    ).order_by("month")

    if monthly_balances.count() == months_diff + 1:
        post_save.connect(
            receiver=create_missing_monthly_balances, sender=MonthlyBalance
        )
        return True, current_month
    else:
        existing_months = set(mb.month for mb in monthly_balances)
        expected_months = [
            add_months(first_monthly_balance.month, i) for i in range(months_diff + 1)
        ]

        missing_months = [
            month for month in expected_months if month not in existing_months
        ]

        for month in missing_months:
            previous_month = month - relativedelta(months=1)

            previous_month_balance = get_month_balance(previous_month)

            transactions_amount_current_month = get_total_amount_transactions_by_month(
                month
            )
            total_previous_monthly_balance = (
                previous_month_balance + transactions_amount_current_month
            )

            created_monthly_balance = MonthlyBalance.objects.create(
                month=month,
                is_first_month=False,
                balance=total_previous_monthly_balance,
            )

        post_save.connect(
            receiver=create_missing_monthly_balances, sender=MonthlyBalance
        )
        return False, current_month
