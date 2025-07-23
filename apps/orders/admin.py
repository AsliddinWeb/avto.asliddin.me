# apps/orders/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.contrib import messages
from .models import Order, OrderItem, OrderStatusHistory
import logging

logger = logging.getLogger(__name__)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product_name', 'total_usd', 'total_som']
    fields = ['product', 'quantity', 'product_name', 'total_usd', 'total_som']


class OrderStatusHistoryInline(admin.TabularInline):
    model = OrderStatusHistory
    extra = 1
    readonly_fields = ['created_at', 'created_by']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'order_number', 'user', 'status', 'total_amount_som',
        'is_paid', 'telegram_status', 'created_at'
    ]
    list_filter = [
        'status', 'created_at', 'oferta_agreed', 'payment_screenshot'
    ]
    search_fields = [
        'order_number', 'user__phone', 'user__first_name'
    ]
    readonly_fields = [
        'order_number', 'total_amount_som', 'created_at', 'updated_at'
    ]
    inlines = [OrderItemInline, OrderStatusHistoryInline]

    fieldsets = (
        ('Asosiy ma\'lumotlar', {
            'fields': ('order_number', 'user', 'status')
        }),
        ('Narx ma\'lumotlari', {
            'fields': ('total_amount_usd', 'total_amount_som', 'usd_rate_used')
        }),
        ('To\'lov ma\'lumotlari', {
            'fields': ('payment_screenshot', 'payment_card_number')
        }),
        ('Yetkazish', {
            'fields': ('delivery_address', 'delivery_phone')
        }),
        ('Oferta', {
            'fields': ('oferta_agreed', 'oferta_agreed_at')
        }),
        ('Qo\'shimcha', {
            'fields': ('admin_notes', 'created_at', 'updated_at')
        }),
    )

    def save_model(self, request, obj, form, change):
        """Admin save qilganda user ma'lumotini saqlash"""
        # Admin userini obj ga qo'shish (signal uchun)
        obj._admin_user = request.user

        # Eski statusni saqlash
        if change and obj.pk:
            try:
                old_obj = Order.objects.get(pk=obj.pk)
                old_status = old_obj.status
                new_status = obj.status

                if old_status != new_status:
                    # Success message
                    messages.success(
                        request,
                        f'Buyurtma #{obj.order_number} holati o\'zgartirildi: '
                        f'{old_status} → {new_status}. '
                        f'Mijozga Telegram orqali xabar yuborildi.'
                    )
                    logger.info(
                        f"Admin {request.user.username} changed order {obj.order_number} status: {old_status} -> {new_status}")
            except Order.DoesNotExist:
                pass

        super().save_model(request, obj, form, change)

    def is_paid(self, obj):
        """To'lov holati ko'rsatish"""
        if obj.payment_screenshot:
            return format_html('<span style="color: green;">✓ To\'langan</span>')
        return format_html('<span style="color: red;">✗ To\'lanmagan</span>')

    is_paid.short_description = 'To\'lov holati'

    def telegram_status(self, obj):
        """Telegram holati ko'rsatish"""
        if obj.user.telegram_chat_id:
            telegram_username = obj.user.telegram_username or "Ulangan"
            return format_html(
                '<span style="color: green;" title="Chat ID: {}">📱 {}</span>',
                obj.user.telegram_chat_id,
                telegram_username
            )
        return format_html('<span style="color: gray;">📵 Ulanmagan</span>')

    telegram_status.short_description = 'Telegram'

    def get_readonly_fields(self, request, obj=None):
        """Dynamic readonly fields"""
        readonly = list(self.readonly_fields)

        # Agar order delivered bo'lsa, ba'zi fieldlarni readonly qilish
        if obj and obj.status == 'delivered':
            readonly.extend(['status', 'total_amount_usd'])

        return readonly

    actions = ['send_test_notification', 'mark_as_confirmed', 'mark_as_shipped']

    def send_test_notification(self, request, queryset):
        """Test notification yuborish"""
        sent_count = 0
        failed_count = 0

        for order in queryset:
            if order.user.telegram_chat_id:
                try:
                    from apps.telegram_auth.notifications import notification_service

                    message = f"""
🔔 <b>Test xabar</b>

📋 <b>Buyurtma:</b> #{order.order_number}
💰 <b>Summa:</b> {order.formatted_total_som}
📊 <b>Holat:</b> {order.get_status_display()}

👨‍💼 <i>Admin: {request.user.get_full_name() or request.user.username}</i>
📅 <i>Vaqt:</i> {order.updated_at.strftime('%d.%m.%Y %H:%M')}

Bu test xabar. Hech qanday amaliyot talab qilinmaydi.
                    """.strip()

                    success = notification_service.send_message_sync(
                        chat_id=order.user.telegram_chat_id,
                        message=message,
                        parse_mode='HTML'
                    )

                    if success:
                        sent_count += 1
                    else:
                        failed_count += 1

                except Exception as e:
                    logger.error(f"Test notification error for order {order.order_number}: {str(e)}")
                    failed_count += 1
            else:
                failed_count += 1

        if sent_count > 0:
            messages.success(request, f'{sent_count} ta buyurtmaga test xabar yuborildi.')
        if failed_count > 0:
            messages.warning(request, f'{failed_count} ta buyurtmaga xabar yuborilmadi (Telegram ulanmagan).')

    send_test_notification.short_description = "Test notification yuborish"

    def mark_as_confirmed(self, request, queryset):
        """Buyurtmalarni tasdiqlangan deb belgilash"""
        updated = 0
        for order in queryset:
            if order.status in ['pending', 'payment_pending']:
                order._admin_user = request.user  # Signal uchun
                order.status = 'confirmed'
                order.save()
                updated += 1

        messages.success(request, f'{updated} ta buyurtma tasdiqlandi va mijozlarga xabar yuborildi.')

    mark_as_confirmed.short_description = "Tasdiqlangan deb belgilash"

    def mark_as_shipped(self, request, queryset):
        """Buyurtmalarni jo'natilgan deb belgilash"""
        updated = 0
        for order in queryset:
            if order.status in ['confirmed', 'preparing']:
                order._admin_user = request.user  # Signal uchun
                order.status = 'shipped'
                order.save()
                updated += 1

        messages.success(request, f'{updated} ta buyurtma jo\'natildi va mijozlarga xabar yuborildi.')

    mark_as_shipped.short_description = "Jo'natilgan deb belgilash"