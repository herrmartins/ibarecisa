from django.db import models
from core.models import BaseModel
from treasury.models import MonthlyReportModel


class MonthlyTransactionByCategoryModel(BaseModel):
    report = models.ForeignKey(MonthlyReportModel, on_delete=models.CASCADE)
    category = models.CharField(max_length=255)
    total_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.0
    )
    is_positive = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Transações mensais por categoria"

    def __str__(self):
        return f'{self.category}'
