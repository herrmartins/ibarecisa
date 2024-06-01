def get_month_balance(month):
    previous_month = month
    from treasury.models import MonthlyBalance
    try:
        balance = MonthlyBalance.objects.get(month=previous_month).balance
    except MonthlyBalance.DoesNotExist:
        return 0
    return balance
