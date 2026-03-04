from django.urls import path
from .views import *

urlpatterns = [
    path('fcm-token/', FcmTokenSaveView.as_view(), name='fcm-token'),
]
