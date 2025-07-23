# apps/orders/apps.py
from django.apps import AppConfig


class OrdersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.orders'
    verbose_name = 'Buyurtmalar'

    def ready(self):
        """App tayyor bo'lganda signals import qilish"""
        import apps.orders.signals  # noqa