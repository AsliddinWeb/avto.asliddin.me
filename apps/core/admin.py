from django.contrib import admin
from modeltranslation.admin import TranslationAdmin
from .models import Settings, Banner


@admin.register(Settings)
class SettingsAdmin(TranslationAdmin):
    list_display = ['usd_rate', 'payment_card_number', 'updated_at']
    readonly_fields = ['created_at', 'updated_at']

    def has_add_permission(self, request):
        return not Settings.objects.exists()


@admin.register(Banner)
class BannerAdmin(TranslationAdmin):
    list_display = ['title', 'is_active', 'order', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['title', 'description']
    list_editable = ['is_active', 'order']
    prepopulated_fields = {'slug': ('title',)}