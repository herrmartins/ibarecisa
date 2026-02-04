from django.contrib import admin
from treasury.models import (
    TransactionModel,
    TransactionEditHistory,
    CategoryModel,
    # REMOVED: MonthlyBalance (replaced by AccountingPeriod)
    MonthlyReportModel,  # Still used for PDF generation
    MonthlyTransactionByCategoryModel,  # Still used for PDF generation
    AccountingPeriod,  # New period model
)
import reversion
from reversion_compare.admin import CompareVersionAdmin

# Register models for versioning
reversion.register(TransactionModel)

admin.site.register(TransactionEditHistory)
admin.site.register(CategoryModel)
# REMOVED: admin.site.register(MonthlyBalance) - replaced by AccountingPeriod
admin.site.register(MonthlyReportModel)
admin.site.register(MonthlyTransactionByCategoryModel)
admin.site.register(AccountingPeriod)


@admin.register(TransactionModel)
class TransactionAdmin(CompareVersionAdmin):
    pass
