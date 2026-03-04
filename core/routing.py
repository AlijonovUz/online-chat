from django.urls import path
from .consumers import MessageConsumer, InboxConsumer, NotificationConsumer

websocket_urlpatterns = [
    path("ws/private/<int:receiver_id>/", MessageConsumer.as_asgi()),
    path("ws/inbox/", InboxConsumer.as_asgi()),
    path("ws/notifications/", NotificationConsumer.as_asgi())
]
