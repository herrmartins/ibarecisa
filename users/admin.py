from django.contrib import admin
from users.models import CustomUser
import reversion
from reversion_compare.admin import CompareVersionAdmin

# Register models for versioning
reversion.register(CustomUser)


@admin.register(CustomUser)
class CustomUserAdmin(CompareVersionAdmin):
    pass
