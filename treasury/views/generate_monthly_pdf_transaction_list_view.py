import weasyprint
from datetime import datetime
from django.http import HttpResponse
from django.template.loader import render_to_string
from treasury.models import TransactionModel, AccountingPeriod
import calendar
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from core.core_context_processor import context_user_data


@login_required
def GenerateMonthlyPDFTransactionListView(
    request, month, year
):
    """
    Gera relatório PDF das transações de um período contábil.

    Args:
        month: Número do mês (1-12)
        year: Ano
    """
    if request.user.has_perm("treasury.view_transactionmodel"):
        # Buscar o período contábil
        try:
            period = AccountingPeriod.objects.get(
                month__year=year,
                month__month=month
            )
        except AccountingPeriod.DoesNotExist:
            return HttpResponseForbidden("Período contábil não encontrado.")

        # Buscar período anterior para saldo inicial
        previous_period = period.get_previous_period()
        previous_balance = previous_period.get_current_balance() if previous_period else period.opening_balance

        # Buscar transações do período
        finance_entries = TransactionModel.objects.filter(
            accounting_period=period,
            transaction_type='original'
        ).order_by("date")

        # Calcular saldos progressivos
        subtotal = []
        balance_for_calc = float(previous_balance)
        for fe in finance_entries:
            balance_for_calc += float(fe.amount)
            subtotal.append(balance_for_calc)

        # Data final do mês anterior
        if previous_period:
            last_month_date = previous_period.last_day
        else:
            _, last_day = calendar.monthrange(year - 1 if month == 1 else year, 12 if month == 1 else month - 1)
            last_month_date = datetime(year - 1 if month == 1 else year, 12 if month == 1 else month - 1, last_day).date()

        context_data = context_user_data(request)
        church_info = context_data.get("church_info")

        # Calcular totais
        total_positive = sum(float(t.amount) for t in finance_entries if t.is_positive)
        total_negative = abs(sum(float(t.amount) for t in finance_entries if not t.is_positive))

        context = {
            "church_info": church_info,
            "finance_entries": finance_entries,
            "subtotal": subtotal,
            "total": balance_for_calc,
            "total_positive": total_positive,
            "total_negative": total_negative,
            "month": month,
            "year": year,
            "month_name": period.month_name,
            "previous_balance": previous_balance,
            "last_month_date": last_month_date,
            "period": period,
        }

        # Render HTML template
        html_string = render_to_string("treasury/monthly_report_pdf.html", context)

        # Get base URL for static files
        base_url = request.build_absolute_uri('/')

        # Generate PDF with WeasyPrint
        weasyprint_html = weasyprint.HTML(string=html_string, base_url=base_url)
        pdf = weasyprint_html.write_pdf()

        if pdf:
            response = HttpResponse(pdf, content_type="application/pdf")
            response[
                "Content-Disposition"
            ] = f'attachment; filename="treasury_report_{month}_{year}.pdf"'
            return response

        return HttpResponse("Failed to generate PDF.", status=500)
    else:
        return HttpResponseForbidden("You don't have permission to access this.")
