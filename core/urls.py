from django.urls import path
from .views import chat_list, private_chat

urlpatterns = [
    path("", chat_list, name="chat_list"),
    path("chat/<str:receiver_username>/", private_chat, name="private_chat"),
]
