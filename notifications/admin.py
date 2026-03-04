from django.contrib import admin

from .models import PushSubscription


@admin.register(PushSubscription)
class PushSubscriptionAdmin(admin.ModelAdmin):
    list_display = ("user", "short_endpoint", "created_at")
    list_filter = ("created_at",)
    search_fields = ("user__username", "user__email", "endpoint")
    readonly_fields = ("user", "endpoint", "p256dh", "auth", "created_at")
    ordering = ("-created_at",)

    def short_endpoint(self, obj):
        return obj.endpoint[:60] + "..."

    short_endpoint.short_description = "Endpoint"
