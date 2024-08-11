def get_monthly_balances_list():
    from treasury.models import MonthlyBalance

    transactions = MonthlyBalance.objects.all().order_by("-month")
    years = transactions.dates("month", "year").distinct()

    return {
        "year_list": [y.year for y in years],
    }
