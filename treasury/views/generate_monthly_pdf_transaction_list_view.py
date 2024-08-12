import weasyprint
from dateutil.relativedelta import relativedelta
from datetime import datetime
from django.http import HttpResponse
import tempfile
from django.template.loader import render_to_string
from treasury.models import TransactionModel, MonthlyBalance
import locale
import calendar
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from core.core_context_processor import context_user_data

@login_required
def GenerateMonthlyPDFTransactionListView(
    request, year=datetime.now().year, month=datetime.now().month
):
    # locale.setlocale(locale.LC_ALL, "pt_BR")
    try:
        locale.setlocale(locale.LC_TIME, "pt_BR.UTF-8")
    except locale.Error:
        print("Locale pt_BR.UTF-8 not available, using default locale.")
    print("Estamos aqui....")
    if request.user.has_perm("treasury.view_transactionmodel"):
        # Pegamos o mês passado
        reports_date = datetime(year, month, day=1)
        monthly_balance_date = reports_date + relativedelta(months=-1)
        last_day_last_month = calendar.monthrange(
            monthly_balance_date.year, monthly_balance_date.month
        )
        subtotal = []
        context_data = context_user_data(request)
        church_info = context_data.get("church_info")

        monthly_balance = MonthlyBalance.objects.get(month=reports_date)

        balance_for_calc = MonthlyBalance.objects.get(
            month=monthly_balance_date
        ).balance
        last_month_balance = balance_for_calc
        finance_entries = TransactionModel.objects.filter(
            date__month=month, date__year=year
        ).order_by(
            "date",
        )
        for fe in finance_entries:
            balance_for_calc += fe.amount
            subtotal.append(balance_for_calc)
            print(
                "Balanço após",
                fe.amount,
                fe.date,
                fe.description,
                ":",
                balance_for_calc,
            )

        context = {
            "church_info": church_info,
            "finance_entries": finance_entries,
            "subtotal": subtotal,
            "total": balance_for_calc,
            "month": reports_date.month,
            "year": reports_date.year,
            "previous_balance": last_month_balance,
            "last_month_date": monthly_balance_date.replace(day=last_day_last_month[1]),
        }

        html_index = render_to_string(
            "treasury/export_pdf_template.html", context)

        base_url = request.build_absolute_uri('/')  # Dynamically determine the base URL
        weasyprint_html = weasyprint.HTML(
            string=html_index, base_url=base_url
        )
        pdf = weasyprint_html.write_pdf(
            stylesheets=[
                weasyprint.CSS(
                    string="body { font-family: serif} img {margin: 10px; width: 40px;}"
                )
            ]
        )

        response = HttpResponse(content_type="application/pdf")
        response["Content-Disposition"] = (
            "attachment; filename=report" + str(datetime.now()) + ".pdf"
        )
        response["Content-Transfer-Encoding"] = "binary"

        with tempfile.NamedTemporaryFile(delete=True) as output:
            output.write(pdf)
            output.flush()
            output.seek(0)
            response.write(output.read())
        return response
    else:
        return HttpResponseForbidden("You don't have permission to access this.")
