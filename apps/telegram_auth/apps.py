from django.apps import AppConfig


class TelegramAuthConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    verbose_name = 'Telegram Login'
    name = 'apps.telegram_auth'
