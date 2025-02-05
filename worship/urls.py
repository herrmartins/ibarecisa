from django.urls import path
from worship.views import (
    WorshipHomeView,
    SongSearchView,
    SongAddView,
    SongDetailView,
    add_song_file,
    SongFileListView
)
from worship.views.search import (
    ComposerListView,
    ThemeListView,
    HymnalListView,
)

app_name = "worship"

urlpatterns = [
    path("", WorshipHomeView.as_view(), name="home"),
    path("songs/search/", SongSearchView.as_view(), name="song-search"),
    path("song-add/", SongAddView.as_view(), name="song-add"),
    path('composers/', ComposerListView.as_view(), name='composer-list'),
    path('themes/', ThemeListView.as_view(), name='song-themes'),
    path('hymnals/', HymnalListView.as_view(), name='hymnal-list'),
    path('song/<int:pk>/', SongDetailView.as_view(), name='song-detail'),
    path('song-files/add/', add_song_file, name='add-song-file'),
    path('song-files/', SongFileListView.as_view(), name='get-song-files'),
]
