from django.urls import path, include
from rest_framework.routers import DefaultRouter

from treasury.api.views import (
    AccountingPeriodViewSet,
    TransactionViewSet,
    ReversalViewSet,
    ReversalCreateView,
    CategoryViewSet,
    PeriodBalanceView,
    MonthlyReportView,
    CurrentBalanceView,
    AccumulatedBalanceBeforeView,
    AuditLogViewSet,
    FrozenReportViewSet,
    ReceiptOCRView,
    ReceiptTransactionCreateView,
    ReceiptMultipleOCRView,
    BatchTransactionCreateView,
)

# Router principal
router = DefaultRouter()
router.register(r'periods', AccountingPeriodViewSet, basename='period')
router.register(r'transactions', TransactionViewSet, basename='transaction')
router.register(r'reversals', ReversalViewSet, basename='reversal')
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'audit', AuditLogViewSet, basename='audit')
router.register(r'frozen-reports', FrozenReportViewSet, basename='frozen-report')

app_name = 'treasury-api'

urlpatterns = [
    # Rotas personalizadas (PRIMEIRO para ter precedência sobre o router)
    path('reversals/create/', ReversalCreateView.as_view(), name='reversal-create'),
    path('ocr/receipt/', ReceiptOCRView.as_view(), name='ocr-receipt'),
    path('ocr/receipt-multiple/', ReceiptMultipleOCRView.as_view(), name='ocr-receipt-multiple'),
    path('transactions/from-receipt/', ReceiptTransactionCreateView.as_view(), name='transaction-from-receipt'),
    path('transactions/batch/', BatchTransactionCreateView.as_view(), name='transaction-batch'),
    path('reports/balance/<int:year>/<int:month>/', PeriodBalanceView.as_view(), name='period-balance'),
    path('reports/monthly/<int:year>/<int:month>/', MonthlyReportView.as_view(), name='monthly-report'),
    path('reports/current-balance/', CurrentBalanceView.as_view(), name='current-balance'),
    path('reports/accumulated-balance-before/<int:year>/<int:month>/', AccumulatedBalanceBeforeView.as_view(), name='accumulated-balance-before'),

    # Rotas do router (DEPOIS para não interceptar rotas específicas)
    path('', include(router.urls)),
]
