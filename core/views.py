from django.db.models import Count, Q
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.contrib.auth import get_user_model
from django.core.cache import cache

User = get_user_model()


def display_name(u):
    return (u.get_full_name() or "").strip() or u.username


@login_required
def chat_list(request):
    me = request.user
    qs = (
        User.objects
        .exclude(id=me.id)
        .annotate(
            unread_count=Count(
                "sent_messages",
                filter=Q(sent_messages__receiver=me, sent_messages__is_read=False),
            )
        )
        .order_by("username")
    )

    users = []
    for user in qs:
        users.append({
            "id": user.id,
            "name": display_name(user),
            "username": user.username,
            "online": bool(cache.get(f"online:{user.id}")),
            "unread": user.unread_count,
            "is_verified": user.is_verified,
        })

    return render(request, "chat_list.html", {
        "me_name": display_name(me),
        "me_id": request.user.id,
        "users": users,
    })


@login_required
def private_chat(request, receiver_username: str):
    receiver = get_object_or_404(User, username=receiver_username)

    receiver_name = display_name(receiver)
    receiver_status = "onlayn" if bool(cache.get(f"online:{receiver.id}")) else "yaqinda onlayn edi"

    return render(request, "chat.html", {
        "receiver_id": receiver.id,
        "receiver_name": receiver_name,
        "receiver_status": receiver_status,
        "me_id": request.user.id,
        "receiver_is_verified": receiver.is_verified,
    })


def login(request):
    return render(request, "registration/login.html")
