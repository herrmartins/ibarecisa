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
    GenerateMonthlyReportView,
    MonthlyReportCreateView,
    MonthlyAnalyticalReportDetailView,
    GenerateMonthlyPDFAnReportView,
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

]
