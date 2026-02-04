from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
import weasyprint
from django.http import HttpResponse, HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from core.core_context_processor import context_user_data
from treasury.models import AccountingPeriod
from decimal import Decimal
from collections import defaultdict


def _is_treasury_user(user):
    """
    Verifica se o usuário é membro da igreja (pode visualizar tesouraria).

    Usuários autorizados:
    - Membro regular (type == REGULAR)
    - Tesoureiro (is_treasurer)
    - Secretário (is_secretary)
    - Pastor (is_pastor)
    - Staff (is_staff)
    - Superuser (is_superuser)
    """
    if not user.is_authenticated:
        return False

    # Membros regulares podem visualizar
    if user.type == "REGULAR":
        return True

    # Staff e funções especiais
    return (
        user.is_treasurer or
        user.is_secretary or
        user.is_pastor or
        user.is_staff or
        user.is_superuser
    )


@login_required
def generate_analytical_report_pdf(request, period_id):
    """
    Gera relatório PDF analítico de um período específico.

    Inclui:
    - Resumo do período
    - Transações detalhadas agrupadas por categoria
    - Balanço do período
    """
    if not _is_treasury_user(request.user):
        return HttpResponseForbidden("Você não tem permissão para acessar este relatório.")

    period = get_object_or_404(AccountingPeriod, pk=period_id)

    # Obter transações do período
    transactions = period.transactions.all().select_related('category')

    # Separar e agrupar por categoria e tipo (positivo/negativo)
    positive_by_category = defaultdict(Decimal)
    negative_by_category = defaultdict(Decimal)

    for transaction in transactions:
        amount = Decimal(str(transaction.amount))
        category_name = transaction.category.name if transaction.category else 'Sem Categoria'
        if amount >= 0:
            positive_by_category[category_name] += amount
        else:
            negative_by_category[category_name] += abs(amount)

    # Calcular totais
    total_p = sum(positive_by_category.values())
    total_n = sum(negative_by_category.values())
    m_result = total_p - total_n

    # Saldo anterior (abertura)
    pm_balance = period.opening_balance if period.opening_balance else Decimal('0')

    # Saldo final
    balance = period.closing_balance if period.closing_balance else (pm_balance + m_result)

    # Contexto com dados da igreja
    context_data = context_user_data(request)
    church_info = context_data.get("church_info")

    context = {
        "church_info": church_info,
        "month": period.month.strftime('%B'),
        "year": period.month.year,
        "date": period.month,
        "pm_balance": pm_balance,
        "total_p": total_p,
        "total_n": total_n,
        "m_result": m_result,
        "balance": balance,
        "p_transactions": dict(positive_by_category) if positive_by_category else None,
        "n_transactions": dict(negative_by_category) if negative_by_category else None,
    }

    html = render_to_string("treasury/export_analytical_report.html", context)
    base_url = request.build_absolute_uri('/')
    weasyprint_html = weasyprint.HTML(string=html, base_url=base_url)
    pdf = weasyprint_html.write_pdf()

    response = HttpResponse(content_type="application/pdf")
    month_str = period.month.strftime('%Y_%m')
    filename = f"relatorio_analitico_{month_str}.pdf"
    response["Content-Disposition"] = f"attachment; filename={filename}"
    response["Content-Transfer-Encoding"] = "binary"

    response.write(pdf)
    return response
