from django.core.exceptions import ValidationError
from treasury.utils import get_aggregate_transactions


def check_financial_data_integrity():
    from treasury.models import MonthlyBalance

    try:
        first_month_balance = MonthlyBalance.objects.get(is_first_month=True)
    except MonthlyBalance.DoesNotExist:
        raise ValidationError("Não há balanço inicial...")

    initial_balance = first_month_balance.balance

    monthly_balances = MonthlyBalance.objects.order_by("month")

    previous_balance = initial_balance

    for monthly_balance in monthly_balances:
        if monthly_balance.is_first_month:
            continue

        year = monthly_balance.month.year
        month = monthly_balance.month.month

        aggregate_transactions = get_aggregate_transactions(year, month)

        expected_balance = previous_balance + aggregate_transactions

        if monthly_balance.balance != expected_balance:
            raise ValidationError(
                f"Dados quebrados: Saldo de {monthly_balance.month} está incorreto. "
                f"Esperado: {expected_balance}, Encontrado: {monthly_balance.balance}"
            )

        previous_balance = monthly_balance.balance

    return "Dados íntegros..."
