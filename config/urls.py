from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from core.views import login

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/login/", login),
    path("accounts/", include('allauth.urls')),
    path("", include("core.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)