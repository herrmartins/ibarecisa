from dateutil.relativedelta import relativedelta


def get_previous_month(date):
    previous_month = date.replace(day=1) - relativedelta(months=1)
    return previous_month
