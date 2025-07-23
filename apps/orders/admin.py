from django.contrib import admin
from django.utils.html import format_html
from .models import Order, OrderItem, OrderStatusHistory


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product_name', 'total_usd', 'total_som']  # price_usd, price_som ni o'chirdik
    fields = ['product', 'quantity', 'product_name', 'total_usd', 'total_som']


class OrderStatusHistoryInline(admin.TabularInline):
    model = OrderStatusHistory
    extra = 1
    readonly_fields = ['created_at', 'created_by']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'order_number', 'user', 'status', 'total_amount_som',
        'is_paid', 'created_at'
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

    def is_paid(self, obj):
        if obj.payment_screenshot:
            return format_html('<span style="color: green;">✓ To\'langan</span>')
        return format_html('<span style="color: red;">✗ To\'lanmagan</span>')

    is_paid.short_description = 'To\'lov holati'