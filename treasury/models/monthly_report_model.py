from django.db import models
from core.models import BaseModel


class MonthlyReportModel(BaseModel):
    month = models.DateField(unique=True)
    previous_month_balance = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.0
    )
    total_positive_transactions = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.0
    )
    total_negative_transactions = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.0
    )
    in_cash = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    in_current_account = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.0
    )
    in_savings_account = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.0
    )
    monthly_result = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    total_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)

    class Meta:
        verbose_name = "Relatório Financeiro Analítico"
        verbose_name_plural = "Relatórios Financeiros Analíticos"

    def __str__(self):
        return f"{self.month}"
