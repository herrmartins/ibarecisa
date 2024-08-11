def monthly_balance_exists(month):
    from treasury.models import MonthlyBalance

    try:
        monthly_balance = MonthlyBalance.objects.get(month=month)
        return True
    except MonthlyBalance.DoesNotExist:
        return False
