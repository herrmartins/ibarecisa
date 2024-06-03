from treasury.models import MonthlyReportModel
from django.template.loader import render_to_string
import weasyprint
from datetime import datetime
from django.http import HttpResponse
import tempfile
import locale
from treasury.utils import get_aggregate_transactions_by_category, get_last_day_of_month
from decimal import Decimal
from django.contrib.auth.decorators import login_required
from core.core_context_processor import context_user_data


@login_required
def GenerateMonthlyPDFAnReportView(request, pk):
    # locale.setlocale(locale.LC_ALL, "pt_BR")
    try:
        locale.setlocale(locale.LC_TIME, "pt_BR.UTF-8")
    except locale.Error:
        print("Locale pt_BR.UTF-8 not available, using default locale.")
    if request.user.has_perm("treasury.view_transactionmodel"):
        an_report = MonthlyReportModel.objects.get(pk=pk)

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
            "total_p": "{:.2f}".format(an_report.total_positive_transactions),
            "total_n": "{:.2f}".format(an_report.total_negative_transactions),
            "m_result": m_result,
            "balance": Decimal(an_report.total_balance),
        }
        html_index = render_to_string("treasury/export_analytical_report.html", context)
        base_url = request.build_absolute_uri('/')
        weasyprint_html = weasyprint.HTML(
            string=html_index, base_url=base_url)
        pdf = weasyprint_html.write_pdf(
            stylesheets=[
                weasyprint.CSS(
                    string="body { font-family: serif} img {margin: 10px; width: 40px;}"
                )
            ]
        )

        response = HttpResponse(content_type="application/pdf")
        response["Content-Disposition"] = (
            "attachment; filename=analytical_report" + str(datetime.now()) + ".pdf"
        )
        response["Content-Transfer-Encoding"] = "binary"

        with tempfile.NamedTemporaryFile(delete=True) as output:
            output.write(pdf)
            output.flush()
            output.seek(0)
            response.write(output.read())
        return response
    else:
        # User doesn't have the required permissions
        return HttpResponse("You don't have the required permissions.")
