# apps/core/context_processors.py
from apps.core.models import Settings
from apps.categories.models import Category
from apps.brands.models import Brand
from django.db.models import Count, Q


def site_settings(request):
    """Global site sozlamalari"""
    try:
        settings = Settings.objects.first()
        return {
            'site_settings': settings,
        }
    except Settings.DoesNotExist:
        return {'site_settings': None}


def header_data(request):
    """Header uchun global ma'lumotlar"""
    try:
        # Header uchun kategoriyalar (eng ko'p 6 ta)
        categories = Category.objects.filter(
            is_active=True,
            parent=None  # faqat parent kategoriyalar
        ).order_by('order')[:6]

        # Header uchun mashhur brendlar (eng ko'p 8 ta)
        popular_brands = Brand.objects.filter(
            is_active=True
        ).annotate(
            products_count=Count('product', filter=Q(product__is_active=True))
        ).order_by('-products_count')[:8]

        return {
            'categories': categories,
            'popular_brands': popular_brands,
        }
    except Exception as e:
        # Xatolik bo'lsa bo'sh qaytarish
        return {
            'categories': [],
            'popular_brands': [],
        }