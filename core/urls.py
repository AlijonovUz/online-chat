from django.urls import path
from .views import chat_list, private_chat

urlpatterns = [
    path("", chat_list, name="chat_list"),
    path("chat/<int:receiver_id>/", private_chat, name="private_chat"),
]
