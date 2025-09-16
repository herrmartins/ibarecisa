from django.contrib import admin
from secretarial.models import (
    MeetingAgendaModel,
    MeetingMinuteModel,
    MinuteTemplateModel,
    MinuteExcerptsModel,
    MinuteProjectModel)
import reversion
from reversion_compare.admin import CompareVersionAdmin

# Register models for versioning
reversion.register(MinuteProjectModel)
reversion.register(MeetingMinuteModel)

admin.site.register(MeetingAgendaModel)
admin.site.register(MinuteTemplateModel)
admin.site.register(MinuteExcerptsModel)


@admin.register(MinuteProjectModel)
class MinuteProjectAdmin(CompareVersionAdmin):
    pass


@admin.register(MeetingMinuteModel)
class MeetingMinuteAdmin(CompareVersionAdmin):
    pass
