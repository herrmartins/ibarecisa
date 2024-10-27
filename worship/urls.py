from django.urls import path
from worship.views import WorshipHomeView, SongSearchView

app_name = "worship"

urlpatterns = [
    path("", WorshipHomeView.as_view(), name="home"),
    path('songs/search/', SongSearchView.as_view(), name='song-search'),
]