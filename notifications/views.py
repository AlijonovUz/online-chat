import json
from pywebpush import WebPushException, webpush

from django.conf import settings
from django.http import JsonResponse
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View

from .models import PushSubscription


class ServiceWorkerView(TemplateView):
    template_name = "service-worker.js"
    content_type = "application/javascript"


class VapidPublicKeyView(LoginRequiredMixin, View):
    def get(self, request):
        return JsonResponse({"vapid_public_key": settings.VAPID_PUBLIC_KEY})


class PushSubscribeView(LoginRequiredMixin, View):
    def post(self, request):
        data = json.loads(request.body)
        endpoint = data.get("endpoint")
        keys = data.get("keys", {})

        PushSubscription.objects.update_or_create(
            user=request.user,
            endpoint=endpoint,
            defaults={
                "p256dh": keys.get("p256dh", ""),
                "auth": keys.get("auth", ""),
            }
        )
        return JsonResponse({"status": "ok"})


def send_push_to_user(user, title: str, body: str, url: str):
    subscriptions = PushSubscription.objects.filter(user=user)

    for sub in subscriptions:
        try:
            webpush(
                subscription_info={
                    "endpoint": sub.endpoint,
                    "keys": {
                        "p256dh": sub.p256dh,
                        "auth": sub.auth,
                    },
                },
                data=json.dumps({"title": title, "body": body, "url": url}),
                vapid_private_key=settings.VAPID_PRIVATE_KEY,
                vapid_claims={"sub": f"mailto:{settings.VAPID_ADMIN_EMAIL}"},
            )
        except WebPushException as e:
            if "410" in str(e) or "404" in str(e):
                sub.delete()
