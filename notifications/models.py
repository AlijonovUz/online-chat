from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class PushSubscription(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="push_subscription"
    )
    fcm_token = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username
