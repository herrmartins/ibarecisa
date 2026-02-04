from django import template
import calendar

register = template.Library()


@register.filter
def month_name(value):
    return calendar.month_name[value]


@register.filter
def format_brl(value):
    """
    Formata valor para formato brasileiro.
    Ex: 1234.56 -> 1.234,56
         10000 -> 10.000,00
    """
    try:
        value = float(value)
        # Primeiro formata com vírgula como separador de milhar e ponto como decimal
        # Depois inverte: ponto para milhar, vírgula para decimal
        formatted = f"{value:,.2f}"
        formatted = formatted.replace(",", "X").replace(".", ",").replace("X", ".")
        return formatted
    except (ValueError, TypeError):
        return "0,00"


@register.filter
def abs_value(value):
    """Retorna o valor absoluto (sem sinal)."""
    try:
        return abs(float(value))
    except (ValueError, TypeError):
        return 0
