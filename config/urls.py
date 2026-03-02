from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings

from core.views import LoginPageView, TermsPageView

urlpatterns = [
    # path("admin/", admin.site.urls),
    path("accounts/login/", LoginPageView.as_view(), name="login"),
    path("accounts/terms/", TermsPageView.as_view(), name="terms"),
    path("accounts/", include('allauth.urls')),
    path("", include("core.urls")),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
