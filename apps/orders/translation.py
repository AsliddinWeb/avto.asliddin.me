# apps/orders/translation.py
from modeltranslation.translator import register, TranslationOptions
from .models import Order, OrderStatusHistory


@register(Order)
class OrderTranslationOptions(TranslationOptions):
    fields = ('admin_notes',)


@register(OrderStatusHistory)
class OrderStatusHistoryTranslationOptions(TranslationOptions):
    fields = ('comment',)