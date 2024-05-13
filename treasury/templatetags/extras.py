from django import template
import calendar

register = template.Library()


@register.filter
def month_name(value):
    return calendar.month_name[value]
