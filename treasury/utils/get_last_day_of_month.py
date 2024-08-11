import calendar
from datetime import datetime


def get_last_day_of_month(year, month):
    last_day = calendar.monthrange(year, month)[1]
    return datetime(year, month, last_day).strftime("%d/%m/%Y")
