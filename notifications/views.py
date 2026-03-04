import json
import firebase_admin
from firebase_admin import credentials, messaging

from django.conf import settings
from django.http import JsonResponse
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View

from .models import PushSubscription

if not firebase_admin._apps:
    cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS)
    firebase_admin.initialize_app(cred)


class ServiceWorkerView(TemplateView):
    template_name = "service-worker/service-worker.js"
    content_type = "application/javascript"

    def render_to_response(self, context, **kwargs):
        r = super().render_to_response(context, **kwargs)
        r["Cache-Control"] = "no-cache, no-store, must-revalidate"
        r["Pragma"] = "no-cache"
        r["Expires"] = "0"
        return r


class FcmTokenSaveView(LoginRequiredMixin, View):
    def post(self, request):
        data = json.loads(request.body)
        fcm_token = data.get("fcm_token")

        if fcm_token:
            sub = PushSubscription.objects.filter(user=request.user).first()
            if sub:
                sub.fcm_token = fcm_token
                sub.save(update_fields=["fcm_token"])
            else:
                PushSubscription.objects.create(
                    user=request.user,
                    fcm_token=fcm_token,
                )
        return JsonResponse({"status": "ok"})


from firebase_admin import messaging


def send_push_to_user(user, title: str, body: str, url: str, image: str = ""):
    subs = PushSubscription.objects.filter(user=user).exclude(fcm_token="").exclude(fcm_token__isnull=True)

    for sub in subs:
        try:
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                ),
                webpush=messaging.WebpushConfig(
                    notification=messaging.WebpushNotification(
                        icon=image or "/static/images/favicon.png",
                    ),
                    fcm_options=messaging.WebpushFCMOptions(
                        link=url
                    ),
                ),
                token=sub.fcm_token,
            )

            messaging.send(message)

        except messaging.UnregisteredError:
            sub.fcm_token = ""
            sub.save(update_fields=["fcm_token"])

        except Exception as e:
            print(f"FCM xatolik: {e}")
