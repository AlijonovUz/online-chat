import json

from django.utils import timezone
from django.core.cache import cache
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async

from core.models import Message, User


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

        last_messages = await self.get_last_messages()
        await self.send(text_data=json.dumps({
            "history": True,
            "messages": last_messages
        }))

        cache.set(f"active:{self.chat_key}:{self.me.id}", True, timeout=600)
        cache.set(self.online_key(self.me.id), True, timeout=600)

        max_id = await self.mark_dialog_read(self.me.id, self.receiver_id)
        if max_id:
            await self.channel_layer.group_send(
                self.group_name,
                {"type": "chat_read", "reader_id": self.me.id, "up_to_id": max_id}
            )

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

        cache.delete(f"active:{self.chat_key}:{self.me.id}")
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

        if data.get('delete'):
            msg_id = int(data.get("message_id", 0))
            if not msg_id:
                return

            ok = await self.delete_message(msg_id, self.me.id, self.receiver_id)
            if ok:
                await self.channel_layer.group_send(
                    self.group_name,
                    {
                        "type": "chat_deleted",
                        "message_id": msg_id,
                        "user_id": self.me.id,
                    }
                )
            return

        if data.get('edit'):
            msg_id = int(data.get('message_id', 0))
            new_text = data.get("message", "").strip()

            if not msg_id or not new_text:
                return

            updated = await self.edit_message(msg_id, self.me.id, self.receiver_id, new_text)

            if updated:
                await self.channel_layer.group_send(
                    self.group_name,
                    {
                        "type": "chat_edited",
                        "message_id": msg_id,
                        "message": updated["message"],
                        "is_edited": True,
                        "user_id": self.me.id,
                    }
                )
            return

        text = data.get('message', "").strip()
        if not text:
            return

        receiver = await self.get_user(self.receiver_id)
        msg_obj = await self.save_message(self.me, receiver, text)

        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "chat_message",
                "id": msg_obj["id"],
                "message": msg_obj['message'],
                "user": self.display_name(self.me),
                "user_id": self.me.id,
                "is_read": msg_obj['is_read'],
                "is_edited": msg_obj["is_edited"],
                "created_at": msg_obj['created_at'],
            }
        )

        if cache.get(f"active:{self.chat_key}:{self.receiver_id}"):
            await self.mark_one_read(msg_obj['id'])
            await self.channel_layer.group_send(
                self.group_name,
                {
                    "type": "chat_read",
                    "reader_id": self.receiver_id,
                    "up_to_id": msg_obj['id']
                }
            )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event))

    async def chat_read(self, event):
        await self.send(text_data=json.dumps({
            "type": "chat_read",
            "reader_id": event['reader_id'],
            "up_to_id": event['up_to_id']
        }))

    async def chat_deleted(self, event):
        await self.send(text_data=json.dumps({
            "type": "chat_deleted",
            "message_id": event['message_id'],
            "user_id": event['user_id'],
        }))

    async def chat_edited(self, event):
        await self.send(text_data=json.dumps({
            "type": "chat_edited",
            "message_id": event["message_id"],
            "message": event["message"],
            "is_edited": event.get("is_edited", True),
            "user_id": event["user_id"],
        }))

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
            "id": message.id,
            "message": message.text,
            "user": self.display_name(message.sender),
            "is_read": message.is_read,
            "is_edited": message.is_edited,
            "created_at": timezone.localtime(message.created_at).strftime("%H:%M"),
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
                "id": m.id,
                "message": m.text,
                "user": self.display_name(m.sender),
                "user_id": m.sender.id,
                "is_read": m.is_read,
                "is_edited": m.is_edited,
                "created_at": timezone.localtime(m.created_at).strftime("%H:%M"),
            }
            for m in qs
        ]

    @sync_to_async
    def mark_one_read(self, msg_id: int):
        Message.objects.filter(id=msg_id, is_read=False).update(is_read=True)

    @sync_to_async
    def mark_dialog_read(self, me_id: int, other_id: int):
        qs = Message.objects.filter(
            sender_id=other_id,
            receiver_id=me_id,
            is_read=False
        )
        max_id = qs.order_by("-id").values_list("id", flat=True).first()
        if max_id:
            qs.update(is_read=True)
        return max_id

    @sync_to_async
    def delete_message(self, msg_id: int, me_id: int, other_id: int):
        qs = Message.objects.filter(
            id=msg_id,
            sender_id__in=[me_id, other_id],
            receiver_id__in=[me_id, other_id]
        )
        msg = qs.first()

        if not msg:
            return False

        if msg.sender_id != me_id:
            return False

        msg.delete()
        return True

    @sync_to_async
    def edit_message(self, msg_id: int, me_id: int, other_id: int, new_text: str):
        qs = Message.objects.filter(
            id=msg_id,
            sender_id__in=[me_id, other_id],
            receiver_id__in=[me_id, other_id]
        )
        msg = qs.first()
        if not msg:
            return None

        if msg.sender_id != me_id:
            return None

        msg.text = new_text
        msg.is_edited = True
        msg.edited_at = timezone.now()
        msg.save(update_fields=["text", "is_edited", "edited_at"])

        return {"message": msg.text}

    def display_name(self, user):
        return (user.get_full_name() or "").strip() or user.username

    def online_key(self, user_id):
        return f"online:{user_id}"

    def last_seen_key(self, user_id):
        return f"last_seen:{user_id}"
