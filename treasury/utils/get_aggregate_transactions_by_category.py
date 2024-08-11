from collections import defaultdict
from decimal import Decimal


def get_aggregate_transactions_by_category(year, month, is_positive=True):
    from treasury.models import TransactionModel

    transactions_filter = {
        "date__year": year,
        "date__month": month,
        "is_positive": is_positive,
    }
    from treasury.models import TransactionModel

    transactions = TransactionModel.objects.filter(
        **transactions_filter
    ).select_related("category")

    transactions_by_category = defaultdict(Decimal)

    for transaction in transactions:
        category_name = transaction.category.name if transaction.category else "outros"

        transactions_by_category[category_name] += Decimal(transaction.amount)

    aggregated_transactions_dict = {
        key: "{:.2f}".format(value) for key, value in transactions_by_category.items()
    }
    return aggregated_transactions_dict
