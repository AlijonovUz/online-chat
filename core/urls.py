from django.urls import path
from .views import *

urlpatterns = [
    path("", HomePageView.as_view(), name="home"),
    path("profile/update/", ProfileUpdateView.as_view(), name="profile-update"),
    path("chats/", ChatListView.as_view(), name="chat-list"),
    path("chats/<str:receiver_username>/", PrivateChatView.as_view(), name="private-chat"),
    path("chats/<str:username>/delete/", ChatDeleteView.as_view(), name="chat-delete"),
    path("search/", SearchUsersView.as_view(), name="search-users"),
]
