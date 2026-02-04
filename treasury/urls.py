from django.urls import path

# New template-based views
from treasury.views.template_views import (
    TreasuryDashboardView,
    PeriodListView,
    PeriodDetailView,
    TransactionListView,
    TransactionDetailView,
    TransactionCreateView,
    TransactionUpdateView,
    TransactionDeleteView,
    BatchTransactionReviewView,
    CategoryListView,
    MonthlyReportView,
    ReversalView,
    BalanceSheetView,
    AuditLogView,
    ChartsView,
)

# PDF generation views (used by new system)
from treasury.views.generate_balance_sheet_pdf_view import GenerateBalanceSheetPDFView
from treasury.views.generate_analytical_report_pdf_view import generate_analytical_report_pdf

app_name = "treasury"

urlpatterns = [
    # ===== MAIN ROUTE =====
    # Point to dashboard instead of old home
    path("", TreasuryDashboardView.as_view(), name="dashboard"),

    # ===== PERIODS =====
    path('periodos/', PeriodListView.as_view(), name='period-list'),
    path('periodos/<int:pk>/', PeriodDetailView.as_view(), name='period-detail'),
    path('periodos/<int:period_id>/pdf/analitico/', generate_analytical_report_pdf, name='period-analytical-pdf'),

    # ===== TRANSACTIONS =====
    path('transacoes/', TransactionListView.as_view(), name='transaction-list'),
    path('transacoes/<int:pk>/', TransactionDetailView.as_view(), name='transaction-detail'),
    path('transacoes/nova/', TransactionCreateView.as_view(), name='transaction-create'),
    path('transacoes/importacao-multipla/', BatchTransactionReviewView.as_view(), name='batch-review'),
    path('transacoes/<int:pk>/editar/', TransactionUpdateView.as_view(), name='transaction-update'),
    path('transacoes/<int:pk>/estornar/', ReversalView.as_view(), name='transaction-reversal'),
    path('transacoes/<int:pk>/excluir/', TransactionDeleteView.as_view(), name='transaction-delete'),

    # ===== REPORTS =====
    path('relatorios/mensal/<int:year>/<int:month>/', MonthlyReportView.as_view(), name='monthly-report'),
    path('relatorios/balanco/', BalanceSheetView.as_view(), name='balance-sheet'),
    path('relatorios/balanco/pdf/', GenerateBalanceSheetPDFView, name='balance-sheet-pdf'),

    # ===== CATEGORIES =====
    path('categorias/', CategoryListView.as_view(), name='category-list'),

    # ===== AUDIT =====
    path('auditoria/', AuditLogView.as_view(), name='audit-log'),

    # ===== CHARTS =====
    path('graficos/', ChartsView.as_view(), name='charts'),
]
