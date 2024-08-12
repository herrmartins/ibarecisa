from django.db.models import Sum


def get_aggregate_transactions(year, month, positive=None):
    from treasury.models import TransactionModel
    transactions = TransactionModel.objects.filter(
        date__year=year, date__month=month
    ).order_by("date")

    if positive is True:
        # Get the sum of positive transactions
        aggregate_amount = (
            transactions.filter(amount__gt=0).aggregate(Sum("amount"))["amount__sum"]
            or 0
        )
    elif positive is False:
        # Get the sum of negative transactions
        aggregate_amount = (
            transactions.filter(amount__lt=0).aggregate(Sum("amount"))["amount__sum"]
            or 0
        )
    else:
        # Get the sum of all transactions
        aggregate_amount = transactions.aggregate(Sum("amount"))["amount__sum"] or 0

    return aggregate_amount
