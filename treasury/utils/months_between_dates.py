from dateutil.rrule import rrule, MONTHLY
from dateutil.relativedelta import relativedelta


def months_between_dates(start_date, end_date):
    end_date = end_date + relativedelta(days=1)
    months = rrule(MONTHLY, dtstart=start_date, until=end_date)
    return months.count() - 1 if months else 0
