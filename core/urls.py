from django.urls import path
from .views import *

urlpatterns = [
    path("", HomePageView.as_view(), name="home"),
    path("chats/", ChatListView.as_view(), name="chat-list"),
    path("chats/<str:receiver_username>/", PrivateChatView.as_view(), name="private-chat"),
    path("search/", SearchUsersView.as_view(), name="search-users"),
]
