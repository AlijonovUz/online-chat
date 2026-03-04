from django.urls import path
from .views import *

urlpatterns = [
    path("vapid-public-key/", VapidPublicKeyView.as_view()),
    path("subscribe/", PushSubscribeView.as_view()),
]
