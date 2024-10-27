from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('user/', include('users.urls')),
    path("accounts/", include("django.contrib.auth.urls")),
    path('secretarial/', include('secretarial.urls')),
    path('treasury/', include('treasury.urls')),
    path('events/', include('events.urls')),
    path("api/", include("api.urls")),
    path("api2/", include("api2.urls")),
    path("blog/", include("blog.urls")),
    path("worship/", include("worship.urls")),
]
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)