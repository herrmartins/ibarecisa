from dateutil.relativedelta import relativedelta


def add_months(start_date, months):
    return start_date + relativedelta(months=months)
