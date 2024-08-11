def update_subsequent_balances(date, difference):
    month = date.replace(day=1)
    from treasury.models import MonthlyBalance

    subsequent_months = MonthlyBalance.objects.filter(month__gt=month)

    for sub_month in subsequent_months:
        sub_month.balance = sub_month.balance + difference
        sub_month.save()
        previous_balance = sub_month.balance
