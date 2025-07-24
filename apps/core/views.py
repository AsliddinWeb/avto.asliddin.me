# apps/core/views.py - KATEGORIYA LOGIKASI TUZATILDI
from django.shortcuts import render, get_object_or_404
from django.views.generic import TemplateView, ListView
from django.http import JsonResponse
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.contrib.postgres.search import TrigramSimilarity

from .models import Settings, Banner
from apps.products.models import Product
from apps.categories.models import Category
from apps.brands.models import Brand


class HomePageView(TemplateView):
    """Bosh sahifa"""
    template_name = 'core/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Active bannerlar
        context['banners'] = Banner.objects.filter(is_active=True).order_by('order')

        # Asosiy kategoriyalar - TUZATILDI
        context['categories'] = Category.objects.filter(
            is_active=True,
            parent=None
        ).prefetch_related(
            'product_set',  # Mahsulotlarni oldindan yuklash
            'subcategories'  # Subcategoriyalarni oldindan yuklash
        ).order_by('order')[:12]

        # Tavsiya qilingan mahsulotlar - 8 ta
        context['featured_products'] = Product.objects.filter(
            is_featured=True,
            is_active=True,
            in_stock=True
        ).select_related('category', 'brand').order_by('?')[:8]

        # Eng ko'p sotilgan mahsulotlar - 8 ta
        context['popular_products'] = Product.objects.filter(
            is_active=True,
            in_stock=True
        ).select_related('category', 'brand').order_by('-views_count')[:8]

        # Eng ko'p like bosilgan mahsulotlar - 8 ta
        context['liked_products'] = Product.objects.filter(
            is_active=True,
            in_stock=True
        ).select_related('category', 'brand').order_by('-likes_count')[:8]

        # Yangi qo'shilgan mahsulotlar - 8 ta (oxirgi 30 kun ichida)
        from datetime import datetime, timedelta
        thirty_days_ago = datetime.now() - timedelta(days=30)
        context['new_products'] = Product.objects.filter(
            is_active=True,
            in_stock=True,
            created_at__gte=thirty_days_ago
        ).select_related('category', 'brand').order_by('-created_at')[:8]

        # Mashhur brendlar - annotation bilan (8 ta)
        context['popular_brands'] = Brand.objects.filter(
            is_active=True
        ).annotate(
            products_count=Count(
                'product',
                filter=Q(product__is_active=True)
            )
        ).order_by('-products_count')[:8]

        # Sayt sozlamalari
        try:
            context['settings'] = Settings.objects.first()
        except:
            context['settings'] = None

        return context


class AboutPageView(TemplateView):
    """Biz haqimizda sahifasi"""
    template_name = 'core/about.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            context['settings'] = Settings.objects.first()
        except:
            context['settings'] = None
        return context


class ContactPageView(TemplateView):
    """Kontakt sahifasi"""
    template_name = 'core/contact.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            context['settings'] = Settings.objects.first()
        except:
            context['settings'] = None
        return context


class OfertaPageView(TemplateView):
    """Oferta sahifasi"""
    template_name = 'core/oferta.html'


def search_view(request):
    """Umumiy qidiruv - typo-tolerant"""
    query = request.GET.get('q', '').strip()
    page = request.GET.get('page', 1)

    context = {
        'query': query,
        'products': [],
        'total_count': 0,
        'categories': [],
        'brands': [],
    }

    if query and len(query) >= 2:
        # Mahsulotlarni qidirish
        products_qs = Product.objects.filter(is_active=True).select_related(
            'category', 'brand'
        )

        # Aniq qidiruv
        exact_products = products_qs.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query)
        )

        # Agar aniq natija kam bo'lsa, similarity search qilish
        if exact_products.count() < 10:
            # Trigram similarity bilan qidiruv (PostgreSQL uchun)
            try:
                similar_products = products_qs.annotate(
                    similarity=TrigramSimilarity('name', query)
                ).filter(similarity__gt=0.1).order_by('-similarity')

                # Exact va similar natijalarni birlashtirish
                product_ids = list(exact_products.values_list('id', flat=True))
                for product in similar_products:
                    if product.id not in product_ids:
                        exact_products = exact_products.union(
                            products_qs.filter(id=product.id)
                        )
            except:
                # Agar PostgreSQL bo'lmasa, oddiy qidiruv
                pass

        # Pagination
        paginator = Paginator(exact_products, 24)  # 24 ta mahsulot per page
        products_page = paginator.get_page(page)

        context['products'] = products_page
        context['total_count'] = paginator.count

        # Kategoriyalarni ham qidirish
        context['categories'] = Category.objects.filter(
            Q(name__icontains=query),
            is_active=True
        )[:5]

        # Brendlarni ham qidirish  
        context['brands'] = Brand.objects.filter(
            Q(name__icontains=query),
            is_active=True
        )[:5]

    return render(request, 'core/search_results.html', context)


def search_suggestions_api(request):
    """Qidiruv suggestions - AJAX"""
    query = request.GET.get('q', '').strip()
    suggestions = []

    if query and len(query) >= 2:
        # Mahsulot nomlari
        products = Product.objects.filter(
            name__icontains=query,
            is_active=True
        ).values_list('name', flat=True)[:5]

        for product_name in products:
            suggestions.append({
                'text': product_name,
                'type': 'product'
            })

        # Kategoriya nomlari
        categories = Category.objects.filter(
            name__icontains=query,
            is_active=True
        ).values_list('name', flat=True)[:3]

        for category_name in categories:
            suggestions.append({
                'text': category_name,
                'type': 'category'
            })

        # Brend nomlari
        brands = Brand.objects.filter(
            name__icontains=query,
            is_active=True
        ).values_list('name', flat=True)[:2]

        for brand_name in brands:
            suggestions.append({
                'text': brand_name,
                'type': 'brand'
            })

    return JsonResponse({'suggestions': suggestions})


class GlobalSearchView(TemplateView):
    """Global qidiruv sahifasi"""
    template_name = 'core/global_search.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = self.request.GET.get('q', '')

        if query:
            # Barcha kategoriyalarda qidirish
            context['products'] = Product.objects.filter(
                Q(name__icontains=query) | Q(description__icontains=query),
                is_active=True
            ).select_related('category', 'brand')[:50]

            context['categories'] = Category.objects.filter(
                name__icontains=query,
                is_active=True
            )[:10]

            context['brands'] = Brand.objects.filter(
                name__icontains=query,
                is_active=True
            )[:10]

        context['query'] = query
        return context

# Error handlers
def handler404(request, exception):
    """Custom 404 error page"""
    return render(request, 'errors/404.html', status=404)

def handler403(request, exception):
    """Custom 403 error page"""
    return render(request, 'errors/403.html', status=403)

def handler500(request):
    """Custom 500 error page"""
    return render(request, 'errors/500.html', status=500)

def handler400(request, exception):
    """Custom 400 error page"""
    return render(request, 'errors/404.html', status=400)  # 404 template ishlatamiz