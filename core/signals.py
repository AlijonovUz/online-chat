from django.dispatch import receiver
from django.db.models.signals import post_save
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from .models import Message


@receiver(post_save, sender=Message)
def notify_inbox(sender, instance: Message, created, update_fields=None, **kwargs):

    if created:
        pass

    elif update_fields and "is_read" in update_fields:
        pass

    else:
        return

    channel_layer = get_channel_layer()

    receiver_id = instance.receiver_id
    sender_id = instance.sender_id

    unread = Message.objects.filter(
        sender_id=sender_id,
        receiver_id=receiver_id,
        is_read=False
    ).count()

    payload = {
        "user_id": sender_id,
        "unread": unread
    }

    async_to_sync(channel_layer.group_send)(
        f"inbox_{receiver_id}",
        {
            "type": "inbox_update",
            "payload": payload
        }
    )
