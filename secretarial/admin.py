from django.contrib import admin
from secretarial.models import (
    MeetingAgendaModel,
    MeetingMinuteModel,
    MinuteTemplateModel,
    MinuteExcerptsModel,
    MinuteProjectModel)
import reversion
from reversion_compare.admin import CompareVersionAdmin

admin.site.register(MeetingAgendaModel)
admin.site.register(MinuteTemplateModel)
admin.site.register(MinuteExcerptsModel)
admin.site.register(MinuteProjectModel)


@admin.register(MeetingMinuteModel)
class MeetingMinuteAdmin(CompareVersionAdmin):
    pass
