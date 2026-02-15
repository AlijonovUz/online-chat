from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Message


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "is_verified",
        "is_staff",
        "is_active",
    )

    list_filter = (
        "is_verified",
        "is_staff",
        "is_superuser",
        "is_active",
    )

    search_fields = ("username", "email", "first_name", "last_name")
    ordering = ("-date_joined",)

    list_editable = ("is_verified",)

    fieldsets = BaseUserAdmin.fieldsets + (
        ("Qo‘shimcha ma'lumotlar", {
            "fields": ("is_verified",),
        }),
    )


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "sender",
        "receiver",
        "short_text",
        "is_read",
        "is_edited",
        "created_at",
    )

    list_filter = (
        "is_read",
        "is_edited",
        "created_at",
    )

    search_fields = (
        "sender__username",
        "receiver__username",
        "text",
    )

    ordering = ("-created_at",)

    readonly_fields = (
        "created_at",
        "edited_at",
    )

    list_select_related = ("sender", "receiver")

    def short_text(self, obj):
        if len(obj.text) > 40:
            return obj.text[:40] + "..."
        return obj.text

    short_text.short_description = "Xabar"

    def has_add_permission(self, request):
        return False
