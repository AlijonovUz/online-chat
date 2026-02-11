import json

from django.utils import timezone
from django.core.cache import cache
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from .models import Message, User


class MessageConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        if self.scope['user'].is_anonymous:
            await self.close()
            return

        self.me = self.scope['user']
        self.receiver_id = int(self.scope['url_route']['kwargs']['receiver_id'])

        a, b = sorted([self.me.id, self.receiver_id])
        self.chat_key = f"pm_{a}_{b}"
        self.group_name = f"chat_{self.chat_key}"

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        cache.set(self.online_key(self.me.id), True, timeout=60)

        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "presence_event",
                "status": "onlayn",
                "user_id": self.me.id,
            }
        )

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

        cache.delete(self.online_key(self.me.id))

        cache.set(
            self.last_seen_key(self.me.id),
            timezone.now().isoformat(),
            timeout=60 * 60 * 24 * 7,
        )

        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "presence_event",
                "status": "yaqinda onlayn edi",
                "user_id": self.me.id,
            }
        )

    async def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data)

        if data.get('typing'):
            await self.channel_layer.group_send(
                self.group_name,
                {
                    "type": "typing_event",
                    "user": self.display_name(self.me),
                    "user_id": self.me.id,
                }
            )
            return

        text = (data.get('message') or "").strip()
        if not text:
            return

        receiver = await self.get_user(self.receiver_id)
        msg_obj = await self.save_message(self.me, receiver, text)

        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "chat_message",
                "message": msg_obj['message'],
                "user": msg_obj['user'],
                "created_at": msg_obj['created_at'],
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event))

    async def typing_event(self, event):
        await self.send(text_data=json.dumps({
            "typing": True,
            "user": event['user'],
            "user_id": event["user_id"],
        }))

    async def presence_event(self, event):
        await self.send(text_data=json.dumps({
            "presence": True,
            "status": event['status'],
            "user_id": event['user_id'],
        }))

    @sync_to_async
    def get_user(self, user_id: int):
        return User.objects.get(id=user_id)

    @sync_to_async
    def save_message(self, sender, receiver, text: str):
        message = Message.objects.create(sender=sender, receiver=receiver, text=text)

        return {
            "message": message.text,
            "user": self.display_name(message.sender),
            "created_at": message.created_at.strftime("%H:%M"),
        }

    @sync_to_async
    def get_last_messages(self):
        qs = Message.objects.filter(
            sender_id__in=[self.me.id, self.receiver_id],
            receiver_id__in=[self.me.id, self.receiver_id],
        ).order_by("-created_at")[:50]
        qs = list(reversed(qs))

        return [
            {
                "message": m.text,
                "user": (m.sender.get_full_name() or "").strip() or m.sender.username,
                "created_at": m.created_at.strftime("%H:%M"),
            }
            for m in qs
        ]

    def display_name(self, user):
        return (user.get_full_name() or "").strip() or user.username

    def online_key(self, user_id):
        return f"online:{user_id}"

    def last_seen_key(self, user_id):
        return f"last_seen:{user_id}"
