from django.contrib import admin
from secretarial.models import (
    MeetingAgendaModel,
    MeetingMinuteModel,
    MinuteTemplateModel,
    MinuteExcerptsModel,
    MinuteProjectModel)

admin.site.register(MeetingAgendaModel)
admin.site.register(MeetingMinuteModel)
admin.site.register(MinuteTemplateModel)
admin.site.register(MinuteExcerptsModel)
admin.site.register(MinuteProjectModel)
