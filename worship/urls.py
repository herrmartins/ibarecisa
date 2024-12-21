from django.urls import path
from worship.views import (
    WorshipHomeView,
    SongSearchView,
    SongAddView,
    SongDetailView,
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
    path("songs/add/", SongAddView.as_view(), name="song-add"),
    path('composers/', ComposerListView.as_view(), name='composer-list'),
    path('themes/', ThemeListView.as_view(), name='song-themes'),
    path('hymnals/', HymnalListView.as_view(), name='hymnal-list'),
    path('song/<int:pk>/', SongDetailView.as_view(), name='song-detail'),
]
