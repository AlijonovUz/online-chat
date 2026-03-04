import json
from channels.generic.websocket import AsyncWebsocketConsumer


class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        if self.scope['user'].is_anonymous:
            await self.close()
            return

        self.me = self.scope['user']
        self.notification_group = f"notifications_{self.me.id}"

        await self.channel_layer.group_add(self.notification_group, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        if hasattr(self, "notification_group"):
            await self.channel_layer.group_discard(self.notification_group, self.channel_name)

    async def new_message_notification(self, event):
        await self.send_json({
            "type": "new_message_notification",
            "sender_id": event["sender_id"],
            "sender_username": event["sender_username"],
            "sender_name": event["sender_name"],
            "sender_avatar": event.get("sender_avatar", ""),
            "message_preview": event["message_preview"],
            "chat_url": event.get("chat_url", ""),
        })

    async def send_json(self, data):
        await self.send(text_data=json.dumps(data))
