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
)

app_name = "treasury"

urlpatterns = [
    path("", TreasuryHomeView.as_view(), name="home"),
    path(
        "balance/first",
        InitialBalanceCreateView.as_view(),
        name="create-initial-balance",
    ),
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
    path("reports/an_report/delete/<int:pk>", AnReportDeleteView.as_view(), name="delete-an_report"),
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
]
