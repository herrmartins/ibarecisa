from django.urls import path
from treasury.views import (
    TreasuryHomeView,
    InitialBalanceCreateView,
    FinanceReportsListView,
    TransactionMonthArchiveView,
    TransactionDetailView,
    TransactionUpdateView,
    TransactionDeleteView,
    GenerateMonthlyPDFTransactionListView,
    GeneratePeriodPDFView,
    GenerateMonthlyReportView,
    MonthlyReportCreateView,
    MonthlyAnalyticalReportDetailView,
    GenerateMonthlyPDFAnReportView,
    GeneratePeriodAnalyticalPDFView,
    AnReportDeleteView,
    CategoryCreateView,
    CategoryFormView,
    CategoryUpdateView,
    CategoriesListView,
    AddTransactionView,
    TransactionListView,
    FinancialDataHealthView,
    GetMonthlyBalancesView,
    FixFinancialDataView,
    FinancialChartsView,
    FinancialAnalysisView,
)
from treasury.views.generate_balance_sheet_pdf_view import GenerateBalanceSheetPDFView

# New template-based views
from treasury.views.template_views import (
    TreasuryDashboardView,
    PeriodListView,
    PeriodDetailView,
    TransactionListView as TemplateTransactionListView,
    TransactionDetailView as TemplateTransactionDetailView,
    TransactionCreateView,
    TransactionUpdateView as TemplateTransactionUpdateView,
    BatchTransactionReviewView,
    CategoryListView as TemplateCategoryListView,
    MonthlyReportView,
    ReversalView,
    BalanceSheetView,
    AuditLogView,
)

app_name = "treasury"

urlpatterns = [
    path("", TreasuryHomeView.as_view(), name="home"),
    path(
        "balance/first",
        InitialBalanceCreateView.as_view(),
        name="create-initial-balance",
    ),
    # Transactions
    path(
        "transaction/<int:pk>",
        TransactionDetailView.as_view(),
        name="transaction-detail",
    ),
    path(
        "transaction/update/<int:pk>",
        TransactionUpdateView.as_view(),
        name="transaction-update",
    ),
    path(
        "transaction/delete/<int:pk>",
        TransactionDeleteView.as_view(),
        name="transaction-delete",
    ),
    # Reports
    path("reports", FinanceReportsListView.as_view(), name="list-financial-reports"),
    path(
        "reports/<int:year>/<int:month>/",
        TransactionMonthArchiveView.as_view(),
        name="monthly-transactions",
    ),
    path(
        "reports/pdf/<int:month>/<int:year>/",
        GenerateMonthlyPDFTransactionListView,
        name="export-pdf-monthly-report",
    ),
    path(
        "reports/an_report/delete/<int:pk>",
        AnReportDeleteView.as_view(),
        name="delete-an_report",
    ),
    path(
        "report/save", MonthlyReportCreateView.as_view(), name="create-monthly-report"
    ),
    path(
        "anreport/<int:pk>",
        MonthlyAnalyticalReportDetailView.as_view(),
        name="analytical-report",
    ),
    path(
        "report/generate/<int:month>/<int:year>/",
        GenerateMonthlyReportView.as_view(),
        name="gen-report",
    ),
    path(
        "anreport/pdf/<int:pk>",
        GenerateMonthlyPDFAnReportView,
        name="export-anreport-pdf",
    ),
    # Novas rotas padronizadas para PDFs (por period_id)
    path(
        "periodos/<int:period_id>/pdf/extrato/",
        GeneratePeriodPDFView,
        name="export-period-extract-pdf",
    ),
    path(
        "periodos/<int:period_id>/pdf/analitico/",
        GeneratePeriodAnalyticalPDFView,
        name="export-period-analytical-pdf",
    ),
    # Categories
    path(
        "category",
        CategoryFormView.as_view(),
        name="category-form",
    ),
    path(
        "category/edit/<int:pk>",
        CategoryUpdateView.as_view(),
        name="edit-category",
    ),
    path(
        "category/create",
        CategoryCreateView.as_view(),
        name="create-category",
    ),
    path(
        "category/update/<int:pk>",
        CategoryUpdateView.as_view(),
        name="update-category",
    ),
    path(
        "category/list",
        CategoriesListView.as_view(),
        name="list-categories",
    ),
    path("add-transaction/", AddTransactionView.as_view(), name="add-transaction"),
    path("transactions/", TransactionListView.as_view(), name="transactions"),
    path("health", FinancialDataHealthView.as_view(), name="check-treasury-health"),
    path('get-balances/', GetMonthlyBalancesView.as_view(), name='monthly-balances-list'),
    path('fix', FixFinancialDataView.as_view(), name='fix-financial-data'),
    path('financial-charts/', FinancialChartsView.as_view(), name='financial-charts'),
    path('analysis/', FinancialAnalysisView.as_view(), name='financial-analysis'),

    # ===== NEW TEMPLATE-BASED VIEWS =====
    # Dashboard
    path('dashboard/', TreasuryDashboardView.as_view(), name='dashboard'),

    # Períodos
    path('periodos/', PeriodListView.as_view(), name='period-list'),
    path('periodos/<int:pk>/', PeriodDetailView.as_view(), name='period-detail'),

    # Transações (new)
    path('transacoes/', TemplateTransactionListView.as_view(), name='transaction-list'),
    path('transacoes/<int:pk>/', TemplateTransactionDetailView.as_view(), name='transaction-detail-new'),
    path('transacoes/nova/', TransactionCreateView.as_view(), name='transaction-create'),
    path('transacoes/importacao-multipla/', BatchTransactionReviewView.as_view(), name='batch-review'),
    path('transacoes/<int:pk>/editar/', TemplateTransactionUpdateView.as_view(), name='transaction-update-new'),
    path('transacoes/<int:pk>/estornar/', ReversalView.as_view(), name='transaction-reversal'),

    # Relatórios
    path('relatorios/mensal/<int:year>/<int:month>/', MonthlyReportView.as_view(), name='monthly-report-new'),
    path('relatorios/balanco/', BalanceSheetView.as_view(), name='balance-sheet'),
    path('relatorios/balanco/pdf/', GenerateBalanceSheetPDFView, name='balance-sheet-pdf'),

    # Categorias (new)
    path('categorias/', TemplateCategoryListView.as_view(), name='category-list'),

    # Auditoria
    path('auditoria/', AuditLogView.as_view(), name='audit-log'),
]
