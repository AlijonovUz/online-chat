import json
from django.core.cache import cache
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.db.models import Q

from core.models import Message

ONLINE_TTL = 70
CONN_TTL = 3600


class InboxConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope["user"]
        if not user.is_authenticated:
            await self.close()
            return

        self.user = user
        self.group_name = f"inbox_{user.id}"

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        count = cache.get(f"conn_count:{user.id}", 0)
        cache.set(f"conn_count:{user.id}", count + 1, timeout=CONN_TTL)

        cache.set(f"online:{user.id}", True, timeout=ONLINE_TTL)

        partner_ids = await self._get_partner_ids(user.id)
        await self._broadcast_presence(partner_ids, online=True)

    async def disconnect(self, code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

        if hasattr(self, "user"):
            count = cache.get(f"conn_count:{self.user.id}", 0)
            new_count = max(0, count - 1)
            cache.set(f"conn_count:{self.user.id}", new_count, timeout=CONN_TTL)

            if new_count == 0:
                cache.delete(f"online:{self.user.id}")
                partner_ids = await self._get_partner_ids(self.user.id)
                await self._broadcast_presence(partner_ids, online=False)

    async def receive(self, text_data=None, bytes_data=None):
        if not text_data:
            return

        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            return

        if data.get("type") == "ping":
            cache.set(f"online:{self.user.id}", True, timeout=ONLINE_TTL)
            await self.send(text_data=json.dumps({"type": "pong"}))

    async def inbox_update(self, event):
        await self.send(text_data=json.dumps({
            "type": "inbox_update",
            "payload": event["payload"]
        }))

    async def presence_update(self, event):
        await self.send(text_data=json.dumps({
            "type": "presence_update",
            "payload": event["payload"]
        }))

    @database_sync_to_async
    def _get_partner_ids(self, me_id: int) -> list[int]:
        qs = (
            Message.objects
            .filter(Q(sender_id=me_id) | Q(receiver_id=me_id))
            .values_list("sender_id", "receiver_id")
            .distinct()
        )

        ids = set()
        for s_id, r_id in qs:
            ids.add(s_id)
            ids.add(r_id)

        ids.discard(me_id)
        return list(ids)

    async def _broadcast_presence(self, partner_ids: list[int], online: bool):
        payload = {"user_id": self.user.id, "online": online}
        for pid in partner_ids:
            await self.channel_layer.group_send(
                f"inbox_{pid}",
                {"type": "presence_update", "payload": payload}
            )