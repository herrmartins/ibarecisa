from django.db.models import Sum


def get_total_amount_transactions_by_month(month):
    from treasury.models import TransactionModel

    month_transactions = TransactionModel.objects.filter(
        date__year=month.year,
        date__month=month.month,
    )

    month_transactions = (
        month_transactions.aggregate(total_amount=Sum("amount"))["total_amount"] or 0
    )
    return month_transactions
