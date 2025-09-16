from django.contrib import admin
from treasury.models import (
    TransactionModel,
    TransactionEditHistory,
    CategoryModel,
    MonthlyBalance,
    MonthlyReportModel,
    MonthlyTransactionByCategoryModel,
)
import reversion
from reversion_compare.admin import CompareVersionAdmin

# Register models for versioning
reversion.register(TransactionModel)

admin.site.register(TransactionEditHistory)
admin.site.register(CategoryModel)
admin.site.register(MonthlyBalance)
admin.site.register(MonthlyReportModel)
admin.site.register(MonthlyTransactionByCategoryModel)


@admin.register(TransactionModel)
class TransactionAdmin(CompareVersionAdmin):
    pass
