from django.contrib import admin
from worship.models import (
    Song,
    SongTheme,
    SongFile,
    Composer,
    Hymnal,
    HymnalAlias,
    WorshipService,
    WorshipServiceSong,
)
import reversion
from reversion_compare.admin import CompareVersionAdmin

# Register models for versioning
reversion.register(Song)
reversion.register(SongTheme)
reversion.register(SongFile)
reversion.register(Composer)
reversion.register(Hymnal)
reversion.register(HymnalAlias)
reversion.register(WorshipService)
reversion.register(WorshipServiceSong)


@admin.register(Song)
class SongAdmin(CompareVersionAdmin):
    pass


@admin.register(SongTheme)
class SongThemeAdmin(CompareVersionAdmin):
    pass


@admin.register(SongFile)
class SongFileAdmin(CompareVersionAdmin):
    pass


@admin.register(Composer)
class ComposerAdmin(CompareVersionAdmin):
    pass


@admin.register(Hymnal)
class HymnalAdmin(CompareVersionAdmin):
    pass


@admin.register(HymnalAlias)
class HymnalAliasAdmin(CompareVersionAdmin):
    pass


@admin.register(WorshipService)
class WorshipServiceAdmin(CompareVersionAdmin):
    pass


@admin.register(WorshipServiceSong)
class WorshipServiceSongAdmin(CompareVersionAdmin):
    pass
