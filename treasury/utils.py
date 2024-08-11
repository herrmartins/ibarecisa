from treasury.models import TransactionModel, CategoryModel
from collections import defaultdict
from decimal import Decimal
import calendar
from datetime import datetime


def get_aggregate_transactions_by_category(year, month, is_positive=True):
    transactions_filter = {
        "date__year": year,
        "date__month": month,
        "is_positive": is_positive,
    }
    transactions = TransactionModel.objects.filter(
        **transactions_filter
    ).select_related("category")

    transactions_by_category = defaultdict(Decimal)

    for transaction in transactions:
        category_name = transaction.category.name if transaction.category else "outros"
        # Ensure the amount is converted to Decimal or float
        transactions_by_category[category_name] += Decimal(transaction.amount)

    aggregated_transactions_dict = {
        key: "{:.2f}".format(value) for key, value in transactions_by_category.items()
    }
    return aggregated_transactions_dict


def get_total_transactions_amount(transactions_dict):
    # Convert values to float before summing them up
    total = sum(float(value) for value in transactions_dict.values())
    return "{:.2f}".format(total)


def get_last_day_of_month(year, month):
    last_day = calendar.monthrange(year, month)[1]
    return datetime(year, month, last_day).strftime("%d/%m/%Y")
