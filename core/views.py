from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views import View
from django.views.generic import ListView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, Count, OuterRef, Subquery, IntegerField, Exists
from django.db.models.functions import Coalesce
from django.core.cache import cache
from django.contrib.auth import get_user_model

from .models import Message
from .mixins import LoginNoRequiredMixin

User = get_user_model()


def display_name(u):
    return (u.get_full_name() or "").strip() or u.username


class ChatListView(LoginRequiredMixin, ListView):
    model = User
    template_name = "chat-list.html"
    context_object_name = "users"

    def get_queryset(self):
        me = self.request.user

        conv_exists = Message.objects.filter(
            Q(sender=OuterRef("pk"), receiver=me) |
            Q(sender=me, receiver=OuterRef("pk"))
        )

        unread_sq = (
            Message.objects
            .filter(sender=OuterRef("pk"), receiver=me, is_read=False)
            .values("sender")
            .annotate(c=Count("id"))
            .values("c")[:1]
        )

        return (
            User.objects
            .exclude(id=me.id)
            .annotate(has_chat=Exists(conv_exists))
            .filter(has_chat=True)
            .annotate(unread_count=Coalesce(Subquery(unread_sq, output_field=IntegerField()), 0))
            .order_by("username")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        users = []

        for user in context["users"]:
            users.append({
                "id": user.id,
                "name": display_name(user),
                "username": user.username,
                "online": bool(cache.get(f"online:{user.id}")),
                "unread": user.unread_count,
                "is_verified": user.is_verified,
            })

        context["users"] = users
        return context


class SearchUsersView(LoginRequiredMixin, View):
    def get(self, request):
        q = (request.GET.get("q") or "").strip()
        if q.startswith("@"):
            q = q[1:]

        if len(q) < 2:
            return JsonResponse({"results": []})

        me = request.user

        qs = (
            User.objects
            .exclude(id=me.id)
            .filter(username__icontains=q)
            .order_by("username")[:20]
        )

        results = []
        for user in qs:
            results.append({
                "username": user.username,
                "name": display_name(user),
                "is_verified": bool(getattr(user, "is_verified", False)),
                "online": bool(cache.get(f"online:{user.id}")),
            })

        return JsonResponse({"results": results})


class PrivateChatView(LoginRequiredMixin, TemplateView):
    template_name = "chat-room.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        receiver = get_object_or_404(
            User,
            username=self.kwargs["receiver_username"]
        )

        context.update({
            "receiver_id": receiver.id,
            "receiver_name": display_name(receiver),
            "receiver_status": (
                "onlayn"
                if bool(cache.get(f"online:{receiver.id}"))
                else "yaqinda onlayn edi"
            ),
            "me_id": self.request.user.id,
            "receiver_is_verified": receiver.is_verified,
        })

        return context


class HomePageView(LoginNoRequiredMixin, TemplateView):
    template_name = "index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['year'] = timezone.now().year

        return context


class LoginPageView(LoginNoRequiredMixin, TemplateView):
    template_name = "registration/login.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['year'] = timezone.now().year

        return context


class TermsPageView(TemplateView):
    template_name = "registration/terms.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['updated_at'] = timezone.now()

        return context