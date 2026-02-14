from django.urls import path
from .views import ChatListView, PrivateChatView, SearchUsersView

urlpatterns = [
    path("", ChatListView.as_view(), name="chat_list"),
    path("search-users/", SearchUsersView.as_view(), name="search_users"),
    path("chat/<str:receiver_username>/", PrivateChatView.as_view(), name="private_chat")
]
