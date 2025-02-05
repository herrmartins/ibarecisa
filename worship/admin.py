from django.contrib import admin
from worship.models import Song, SongTheme, SongFile, Composer, Hymnal

admin.site.register(Song)
admin.site.register(SongTheme)
admin.site.register(SongFile)
admin.site.register(Composer)
admin.site.register(Hymnal)