from dateutil.relativedelta import relativedelta
from treasury.exceptions import NoInitialMonthlyBalance
import datetime
from django.utils import timezone


def check_and_create_missing_balances(date):
    from treasury.models import MonthlyBalance
    current_datetime = datetime.datetime.now()
    current_datetime = timezone.make_aware(current_datetime)
    current_date = current_datetime.date()

    current_month = current_date.replace(day=1)
    from treasury.models import MonthlyBalance
    first_monthly_balance = MonthlyBalance.objects.filter(
        is_first_month=True).first()

    if not first_monthly_balance:
        raise NoInitialMonthlyBalance("Você precisa criar um balanço inicial...")

    from treasury.utils import months_between_dates
    months_diff = months_between_dates(
        first_monthly_balance.month, current_month)

    monthly_balances = MonthlyBalance.objects.filter(
        month__range=(first_monthly_balance.month, current_month)
    ).order_by("month")

    if monthly_balances.count() == months_diff + 1:
        pass

    else:
        from treasury.utils import add_months
        existing_months = set(mb.month for mb in monthly_balances)
        expected_months = [
            add_months(first_monthly_balance.month, i) for i in range(months_diff + 1)
        ]

        missing_months = [
            month for month in expected_months if month not in existing_months
        ]

        for month in missing_months:
            if not MonthlyBalance.objects.filter(month=month).exists():
                previous_month = month - relativedelta(months=1)

                from treasury.utils import get_month_balance, get_total_amount_transactions_by_month
                previous_month_balance = get_month_balance(previous_month)

                transactions_amount_current_month = get_total_amount_transactions_by_month(
                    month
                )
                total_previous_monthly_balance = (
                    previous_month_balance + transactions_amount_current_month
                )

                created_monthly_balance = MonthlyBalance.objects.create(
                    month=month,
                    balance=total_previous_monthly_balance,
                )
