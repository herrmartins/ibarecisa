from django.core.exceptions import ValidationError
from treasury.utils import get_aggregate_transactions


def check_financial_data_integrity():
    from treasury.models import MonthlyBalance

    results = []
    try:
        first_month_balance = MonthlyBalance.objects.get(is_first_month=True)
        initial_balance = first_month_balance.balance
    except MonthlyBalance.DoesNotExist:
        return "Não há balanço inicial...", results
    except Exception as e:
        return f"Erro ao obter balanço inicial: {str(e)}", results

    try:
        monthly_balances = MonthlyBalance.objects.order_by("month")
        previous_balance = initial_balance
        integrity_message = "Dados íntegros..."

        for monthly_balance in monthly_balances:
            if monthly_balance.is_first_month:
                results.append(
                    {
                        "month": monthly_balance.month,
                        "balance": monthly_balance.balance,
                        "expected_balance": monthly_balance.balance,
                        "aggregate_transactions": 0,
                        "integrity": True,
                    }
                )
                continue

            year = monthly_balance.month.year
            month = monthly_balance.month.month

            try:
                aggregate_transactions = get_aggregate_transactions(year, month)
            except Exception as e:
                results.append(
                    {
                        "month": monthly_balance.month,
                        "balance": monthly_balance.balance,
                        "expected_balance": "Erro ao calcular",
                        "aggregate_transactions": "Erro ao calcular",
                        "integrity": False,
                    }
                )
                integrity_message = f"Erro ao calcular transações agregadas para {monthly_balance.month}: {str(e)}"
                continue

            expected_balance = previous_balance + aggregate_transactions

            if monthly_balance.balance != expected_balance:
                integrity_message = (
                    f"Dados quebrados: Saldo de {monthly_balance.month} está incorreto. "
                    f"Esperado: {expected_balance}, Encontrado: {monthly_balance.balance}"
                )
                results.append(
                    {
                        "month": monthly_balance.month,
                        "balance": monthly_balance.balance,
                        "expected_balance": expected_balance,
                        "aggregate_transactions": aggregate_transactions,
                        "integrity": False,
                    }
                )
            else:
                results.append(
                    {
                        "month": monthly_balance.month,
                        "balance": monthly_balance.balance,
                        "expected_balance": expected_balance,
                        "aggregate_transactions": aggregate_transactions,
                        "integrity": True,
                    }
                )

            previous_balance = monthly_balance.balance
    except Exception as e:
        return f"Erro ao verificar a integridade dos dados: {str(e)}", results

    return integrity_message, results
