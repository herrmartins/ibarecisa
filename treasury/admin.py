from django.contrib import admin
from treasury.models import (
    TransactionModel,
    TransactionEditHistory,
    CategoryModel,
    MonthlyBalance,
    MonthlyReportModel,
    MonthlyTransactionByCategoryModel,
)

admin.site.register(TransactionEditHistory)
admin.site.register(CategoryModel)
admin.site.register(MonthlyBalance)
admin.site.register(MonthlyReportModel)
admin.site.register(MonthlyTransactionByCategoryModel)
admin.site.register(TransactionModel)
