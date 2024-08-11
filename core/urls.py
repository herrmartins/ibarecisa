from django.urls import path
from .views import IndexView, ConfigView, AboutView

app_name = "core"

urlpatterns = [
    path("", IndexView.as_view(), name="home"),
    path("config", ConfigView.as_view(), name="config"),
    path("about", AboutView.as_view(), name="about"),
]
