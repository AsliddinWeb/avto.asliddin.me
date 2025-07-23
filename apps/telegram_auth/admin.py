from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import UserCode


@admin.register(UserCode)
class UserCodeAdmin(admin.ModelAdmin):
    list_display = [
        'phone', 'code', 'telegram_chat_id', 'telegram_username',
        'is_used', 'created_at'
    ]
    list_filter = ['is_used', 'created_at']
    search_fields = ['phone', 'code', 'telegram_username']
    readonly_fields = ['code', 'created_at']
    ordering = ['-created_at']

    def has_add_permission(self, request):
        return False  # Faqat sistem yaratadi

    def has_change_permission(self, request, obj=None):
        return False  # O'zgartirishni cheklash