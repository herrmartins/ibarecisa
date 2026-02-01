from treasury.models import AccountingPeriod
from django.template.loader import render_to_string
import weasyprint
from django.http import HttpResponse, HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from core.core_context_processor import context_user_data
from decimal import Decimal


@login_required
def GenerateBalanceSheetPDFView(request):
    """
    Gera relatório PDF do balanço financeiro com filtros.

    Query params:
        start_year: Ano inicial
        end_year: Ano final
        status: Filtro de status (all, open, closed, archived)
    """
    if not request.user.has_perm("treasury.view_accountingperiod"):
        return HttpResponseForbidden("You don't have the required permissions.")

    # Obter parâmetros de filtro
    start_year = request.GET.get('start_year')
    end_year = request.GET.get('end_year')
    status_filter = request.GET.get('status', 'all')

    # Buscar períodos com filtros
    periods = AccountingPeriod.objects.all().order_by('month')

    if start_year:
        periods = periods.filter(month__year__gte=int(start_year))
    if end_year:
        periods = periods.filter(month__year__lte=int(end_year))
    if status_filter and status_filter != 'all':
        periods = periods.filter(status=status_filter)

    # Calcular o saldo acumulado ANTES do primeiro período filtrado
    running_balance = Decimal('0.00')
    if periods.exists():
        first_period = periods.first()

        # Buscar todos os períodos anteriores ao primeiro filtrado
        previous_periods = AccountingPeriod.objects.filter(
            month__lt=first_period.month
        ).order_by('month')

        # Somar o resultado de todos os períodos anteriores
        for prev_period in previous_periods:
            summary = prev_period.get_transactions_summary()
            total_pos = Decimal(str(summary.get('total_positive', 0)))
            total_neg = Decimal(str(summary.get('total_negative', 0)))
            net = total_pos + total_neg
            # Se tem closing_balance, usa ele
            if prev_period.closing_balance is not None:
                running_balance = prev_period.closing_balance
            else:
                running_balance += net

    # Calcular saldos acumulados para os períodos filtrados
    periods_with_balance = []
    total_positive = Decimal('0.00')
    total_negative = Decimal('0.00')

    for period in periods:
        summary = period.get_transactions_summary()
        opening_balance = running_balance
        total_pos = Decimal(str(summary.get('total_positive', 0)))
        total_neg = Decimal(str(summary.get('total_negative', 0)))
        net = total_pos + total_neg

        # Se o período está fechado, usa closing_balance, senão calcula
        if period.closing_balance is not None:
            closing_balance = period.closing_balance
        else:
            closing_balance = running_balance + net

        periods_with_balance.append({
            'period': period,
            'opening_balance': opening_balance,
            'total_positive': total_pos,
            'total_negative': total_neg,
            'net': net,
            'closing_balance': closing_balance,
        })

        running_balance = closing_balance
        total_positive += total_pos
        total_negative += total_neg

    total_net = total_positive + total_negative
    final_balance = running_balance

    # Label do status
    status_labels = {
        'all': 'Todos',
        'open': 'Abertos',
        'closed': 'Fechados',
        'archived': 'Arquivados',
    }

    # Contexto com dados da igreja
    context_data = context_user_data(request)
    church_info = context_data.get("church_info")

    context = {
        "church_info": church_info,
        "start_year": start_year,
        "end_year": end_year,
        "status_filter": status_filter,
        "status_label": status_labels.get(status_filter, 'Todos'),
        "periods_with_balance": periods_with_balance,
        "total_positive": total_positive,
        "total_negative": total_negative,
        "total_net": total_net,
        "final_balance": final_balance,
    }

    html = render_to_string("treasury/export_balance_sheet_report.html", context)
    base_url = request.build_absolute_uri('/')
    weasyprint_html = weasyprint.HTML(string=html, base_url=base_url)
    pdf = weasyprint_html.write_pdf()

    response = HttpResponse(content_type="application/pdf")
    filename = f"balanco_financeiro_{start_year}_{end_year}.pdf"
    response["Content-Disposition"] = f"attachment; filename={filename}"
    response["Content-Transfer-Encoding"] = "binary"

    response.write(pdf)
    return response
