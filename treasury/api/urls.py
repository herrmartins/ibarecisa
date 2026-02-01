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
    AuditLogViewSet,
)

# Router principal
router = DefaultRouter()
router.register(r'periods', AccountingPeriodViewSet, basename='period')
router.register(r'transactions', TransactionViewSet, basename='transaction')
router.register(r'reversals', ReversalViewSet, basename='reversal')
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'audit', AuditLogViewSet, basename='audit')

app_name = 'treasury-api'

urlpatterns = [
    # Rotas do router
    path('', include(router.urls)),

    # Rotas personalizadas
    path('reversals/create/', ReversalCreateView.as_view(), name='reversal-create'),

    # Relatórios
    path('reports/balance/<int:year>/<int:month>/', PeriodBalanceView.as_view(), name='period-balance'),
    path('reports/monthly/<int:year>/<int:month>/', MonthlyReportView.as_view(), name='monthly-report'),
    path('reports/current-balance/', CurrentBalanceView.as_view(), name='current-balance'),
]
