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
    qs = User.objects.exclude(id=me.id).order_by("username")

    users = []
    for u in qs:
        users.append({
            "id": u.id,
            "name": display_name(u),
            "username": u.username,
            "online": bool(cache.get(f"online:{u.id}")),
        })

    return render(request, "chat_list.html", {
        "me_name": display_name(me),
        "users": users,
    })

@login_required
def private_chat(request, receiver_id: int):
    receiver = get_object_or_404(User, id=receiver_id)

    receiver_name = display_name(receiver)
    receiver_status = "onlayn" if bool(cache.get(f"online:{receiver.id}")) else "yaqinda onlayn edi"

    return render(request, "chat.html", {
        "receiver_id": receiver_id,
        "receiver_name": receiver_name,
        "receiver_status": receiver_status,
        "me_name": display_name(request.user),
    })
