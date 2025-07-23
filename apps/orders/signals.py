# apps/orders/signals.py
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Order, OrderStatusHistory
import logging
import threading

logger = logging.getLogger(__name__)
User = get_user_model()


@receiver(pre_save, sender=Order)
def order_status_change_pre_save(sender, instance, **kwargs):
    """Order status o'zgarishini kuzatish (oldingi holatni saqlash)"""
    if instance.pk:  # Agar update bo'lsa
        try:
            old_instance = Order.objects.get(pk=instance.pk)
            instance._old_status = old_instance.status
        except Order.DoesNotExist:
            instance._old_status = None
    else:
        instance._old_status = None


@receiver(post_save, sender=Order)
def order_status_change_post_save(sender, instance, created, **kwargs):
    """Order status o'zgarganidan keyin Telegram xabar yuborish"""

    # Yangi buyurtma bo'lsa hech narsa qilmaymiz
    if created:
        return

    # Eski status mavjud bo'lsa va o'zgargan bo'lsa
    old_status = getattr(instance, '_old_status', None)
    new_status = instance.status

    if old_status and old_status != new_status:
        logger.info(f"Order {instance.order_number} status changed: {old_status} -> {new_status}")

        # Admin userini aniqlash (request dan)
        admin_user = getattr(instance, '_admin_user', None)

        # OrderStatusHistory yaratish
        OrderStatusHistory.objects.create(
            order=instance,
            status=new_status,
            comment=f"Status o'zgartirildi: {old_status} -> {new_status}",
            created_by=admin_user
        )

        # Telegram notification yuborish (alohida thread da)
        def send_notification():
            try:
                from apps.telegram_auth.notifications import notification_service
                notification_service.send_order_status_notification(
                    order=instance,
                    old_status=old_status,
                    new_status=new_status,
                    admin_user=admin_user
                )
            except Exception as e:
                logger.error(f"Failed to send telegram notification: {str(e)}")

        # Background thread da yuborish (blocking bo'lmasligi uchun)
        notification_thread = threading.Thread(target=send_notification)
        notification_thread.daemon = True
        notification_thread.start()


@receiver(post_save, sender=Order)
def payment_screenshot_notification(sender, instance, created, **kwargs):
    """To'lov cheki yuklanganda notification"""

    if not created and instance.payment_screenshot:
        # Agar payment_screenshot yangi qo'shilgan bo'lsa
        if not hasattr(instance, '_old_payment_screenshot'):
            try:
                old_instance = Order.objects.get(pk=instance.pk)
                if not old_instance.payment_screenshot and instance.payment_screenshot:
                    # Payment confirmation notification
                    def send_payment_notification():
                        try:
                            from apps.telegram_auth.notifications import notification_service
                            notification_service.send_payment_confirmation_notification(instance)
                        except Exception as e:
                            logger.error(f"Failed to send payment notification: {str(e)}")

                    notification_thread = threading.Thread(target=send_payment_notification)
                    notification_thread.daemon = True
                    notification_thread.start()
            except Order.DoesNotExist:
                pass