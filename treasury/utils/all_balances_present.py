from django.utils import timezone
from treasury.exceptions import NoInitialMonthlyBalance


def all_balances_present():
    from treasury.models import MonthlyBalance

    current_month = timezone.now().date().replace(day=1)
    from treasury.models import MonthlyBalance

    first_monthly_balance = MonthlyBalance.objects.filter(is_first_month=True).first()
    if not first_monthly_balance:
        raise NoInitialMonthlyBalance("You must create the initial balance...")

    from treasury.utils import months_between_dates

    months_diff = months_between_dates(first_monthly_balance.month, current_month)

    monthly_balances = MonthlyBalance.objects.filter(
        month__range=(first_monthly_balance.month, current_month)
    ).order_by("month")
    if monthly_balances.count() == months_diff + 1:
        return True
    else:
        return False
