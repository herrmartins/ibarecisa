def get_total_transactions_amount(transactions_dict):
    # Convert values to float before summing them up
    total = sum(float(value) for value in transactions_dict.values())
    return "{:.2f}".format(total)
