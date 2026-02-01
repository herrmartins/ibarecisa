from treasury.models import MonthlyReportModel, AccountingPeriod
from django.template.loader import render_to_string
import weasyprint
from datetime import datetime
from django.http import HttpResponse, HttpResponseForbidden
import tempfile
import locale
from treasury.utils import get_aggregate_transactions_by_category, get_last_day_of_month
from decimal import Decimal
from django.contrib.auth.decorators import login_required
from core.core_context_processor import context_user_data


@login_required
def GeneratePeriodAnalyticalPDFView(request, period_id):
    """
    Gera relatório PDF analítico de um período contábil.

    Args:
        period_id: ID do AccountingPeriod
    """
    try:
        locale.setlocale(locale.LC_TIME, "pt_BR.UTF-8")
    except locale.Error:
        print("Locale pt_BR.UTF-8 not available, using default locale.")

    if not request.user.has_perm("treasury.view_transactionmodel"):
        return HttpResponseForbidden("You don't have the required permissions.")

    # Buscar o período contábil
    try:
        period = AccountingPeriod.objects.get(pk=period_id)
    except AccountingPeriod.DoesNotExist:
        return HttpResponseForbidden("Período contábil não encontrado.")

    # Buscar ou criar o relatório analítico correspondente
    an_report, created = MonthlyReportModel.objects.get_or_create(
        month=period.month,
        defaults={
            'previous_month_balance': Decimal('0.00'),
            'total_positive_transactions': Decimal('0.00'),
            'total_negative_transactions': Decimal('0.00'),
            'monthly_result': Decimal('0.00'),
            'total_balance': Decimal('0.00'),
        }
    )

    # Se foi criado agora ou está com valores zerados, recalcular
    if created or (an_report.total_positive_transactions == 0 and an_report.total_negative_transactions == 0):
        period._create_monthly_report()
        an_report = MonthlyReportModel.objects.get(month=period.month)

    reports_month = an_report.month.month
    reports_year = an_report.month.year
    last_day = get_last_day_of_month(reports_year, reports_month)

    positive_transactions_dict = get_aggregate_transactions_by_category(
        reports_year, reports_month, True
    )
    negative_transactions_dict = get_aggregate_transactions_by_category(
        reports_year, reports_month, False
    )

    m_result = (
        an_report.total_positive_transactions
        + an_report.total_negative_transactions
    )
    context_data = context_user_data(request)
    church_info = context_data.get("church_info")

    context = {
        "church_info": church_info,
        "date": last_day,
        "year": reports_year,
        "month": reports_month,
        "pm_balance": an_report.previous_month_balance,
        "report": an_report,
        "p_transactions": positive_transactions_dict,
        "n_transactions": negative_transactions_dict,
        "total_p": an_report.total_positive_transactions,
        "total_n": an_report.total_negative_transactions,
        "m_result": m_result,
        "balance": Decimal(an_report.total_balance),
    }
    html_index = render_to_string("treasury/export_analytical_report.html", context)
    base_url = request.build_absolute_uri('/')
    weasyprint_html = weasyprint.HTML(
        string=html_index, base_url=base_url)
    pdf = weasyprint_html.write_pdf()

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = (
        f"attachment; filename=relatorio_analitico_{reports_month}_{reports_year}.pdf"
    )
    response["Content-Transfer-Encoding"] = "binary"

    with tempfile.NamedTemporaryFile(delete=True) as output:
        output.write(pdf)
        output.flush()
        output.seek(0)
        response.write(output.read())
    return response
