from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = [
        'phone', 'first_name', 'last_name', 'is_phone_verified',
        'telegram_status', 'date_joined', 'is_active'
    ]
    list_filter = [
        'is_phone_verified', 'is_active', 'is_staff', 'date_joined'
    ]
    search_fields = ['phone', 'first_name', 'last_name', 'telegram_username']
    ordering = ['-date_joined']

    fieldsets = (
        (None, {'fields': ('phone', 'password')}),
        ('Shaxsiy ma\'lumotlar', {
            'fields': ('first_name', 'last_name', 'email')
        }),
        ('Telegram ma\'lumotlar', {
            'fields': ('telegram_chat_id', 'telegram_username', 'is_phone_verified')
        }),
        ('Ruxsatlar', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Muhim sanalar', {
            'fields': ('last_login', 'date_joined', 'created_at', 'updated_at')
        }),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('phone', 'first_name', 'password1', 'password2'),
        }),
    )

    readonly_fields = ['created_at', 'updated_at', 'date_joined', 'last_login']

    def telegram_status(self, obj):
        if obj.telegram_chat_id:
            return format_html(
                '<span style="color: green;">✅ {})</span>',
                obj.telegram_username or 'Ulangan'
            )
        return format_html('<span style="color: gray;">❌ Ulanmagan</span>')

    telegram_status.short_description = 'Telegram'
