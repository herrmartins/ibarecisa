from django.urls import path
from worship.views import (
    WorshipHomeView,
    SongSearchView,
    ThemeListView,
    ComposerListView,
    SongAddView,
)

app_name = "worship"

urlpatterns = [
    path("", WorshipHomeView.as_view(), name="home"),
    path("songs/search/", SongSearchView.as_view(), name="song-search"),
    path("songs/add/", SongAddView.as_view(), name="song-add"),
    path('composers/search', ComposerListView.as_view(), name='composer-list'),
    path('themes/search', ThemeListView.as_view(), name='theme-list'),
]
