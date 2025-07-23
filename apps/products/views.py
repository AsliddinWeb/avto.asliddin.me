# apps/products/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView
from django.core.paginator import Paginator
from django.db.models import Q, Count, Avg
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.decorators.http import require_POST
from django.contrib.postgres.search import TrigramSimilarity

from .models import Product, ProductImage, UserLike
from apps.categories.models import Category
from apps.brands.models import Brand, CarModel
from apps.reviews.models import Review, ProductWishlist

from django.views.decorators.http import require_http_methods
import json

class ProductListView(ListView):
    """Barcha mahsulotlar ro'yxati"""
    model = Product
    template_name = 'products/product_list.html'
    context_object_name = 'products'
    paginate_by = 24

    def get_queryset(self):
        # Filter parametrlari
        category_filter = self.request.GET.get('category')
        brand_filter = self.request.GET.get('brand')
        price_min = self.request.GET.get('price_min')
        price_max = self.request.GET.get('price_max')
        sort_by = self.request.GET.get('sort', '-created_at')
        in_stock = self.request.GET.get('in_stock')

        # Base queryset
        queryset = Product.objects.filter(is_active=True).select_related(
            'category', 'brand'
        )

        # Filters
        if category_filter:
            queryset = queryset.filter(category__slug=category_filter)

        if brand_filter:
            queryset = queryset.filter(brand__slug=brand_filter)

        if price_min:
            queryset = queryset.filter(price_usd__gte=price_min)

        if price_max:
            queryset = queryset.filter(price_usd__lte=price_max)

        if in_stock == '1':
            queryset = queryset.filter(in_stock=True)

        # Sorting
        sort_options = {
            'name': 'name',
            '-name': '-name',
            'price': 'price_usd',
            '-price': '-price_usd',
            'popular': '-views_count',
            'liked': '-likes_count',
            'newest': '-created_at',
            'oldest': 'created_at',
        }

        if sort_by in sort_options:
            queryset = queryset.order_by(sort_options[sort_by])

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Filter options
        context['categories'] = Category.objects.filter(
            is_active=True
        ).order_by('name')

        context['brands'] = Brand.objects.filter(
            is_active=True
        ).order_by('name')

        # Current filters
        context['current_category'] = self.request.GET.get('category')
        context['current_brand'] = self.request.GET.get('brand')
        context['current_sort'] = self.request.GET.get('sort', '-created_at')
        context['price_min'] = self.request.GET.get('price_min')
        context['price_max'] = self.request.GET.get('price_max')
        context['in_stock_filter'] = self.request.GET.get('in_stock')

        return context


class ProductDetailView(DetailView):
    """Mahsulot detali sahifasi"""
    model = Product
    template_name = 'products/product_detail.html'
    context_object_name = 'product'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def get_queryset(self):
        return Product.objects.filter(is_active=True).select_related(
            'category', 'brand'
        ).prefetch_related(
            'images', 'car_models'
        )

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        # Views count ni oshirish
        obj.views_count += 1
        obj.save(update_fields=['views_count'])
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.object

        # Mahsulot qo'shimcha rasmlari
        context['product_images'] = product.images.all().order_by('order')

        # Mos avtomobil modellari
        context['compatible_models'] = product.car_models.filter(is_active=True)

        # Mahsulot sharhlari
        context['reviews'] = Review.objects.filter(
            product=product,
            is_approved=True
        ).select_related('user').order_by('-created_at')

        # Sharhlar statistikasi
        reviews_stats = context['reviews'].aggregate(
            avg_rating=Avg('rating'),
            total_reviews=Count('id')
        )
        context['avg_rating'] = reviews_stats['avg_rating'] or 0
        context['total_reviews'] = reviews_stats['total_reviews']

        # Foydalanuvchi bu mahsulotni like qilganmi
        if self.request.user.is_authenticated:
            context['user_liked'] = UserLike.objects.filter(
                user=self.request.user,
                product=product
            ).exists()

            context['user_wishlisted'] = ProductWishlist.objects.filter(
                user=self.request.user,
                product=product
            ).exists()
        else:
            context['user_liked'] = False
            context['user_wishlisted'] = False

        # O'xshash mahsulotlar (bir xil kategoriya)
        context['related_products'] = Product.objects.filter(
            category=product.category,
            is_active=True,
            in_stock=True
        ).exclude(
            id=product.id
        ).select_related('category', 'brand')[:8]

        # Bir xil brenddagi mahsulotlar
        if product.brand:
            context['brand_products'] = Product.objects.filter(
                brand=product.brand,
                is_active=True,
                in_stock=True
            ).exclude(
                id=product.id
            ).select_related('category', 'brand')[:6]

        return context


class ProductSearchView(ListView):
    """Mahsulot qidiruv - typo-tolerant"""
    model = Product
    template_name = 'products/product_search.html'
    context_object_name = 'products'
    paginate_by = 24

    def get_queryset(self):
        query = self.request.GET.get('q', '').strip()

        if not query or len(query) < 2:
            return Product.objects.none()

        # Base queryset
        queryset = Product.objects.filter(is_active=True).select_related(
            'category', 'brand'
        )

        # Aniq qidiruv
        exact_results = queryset.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(category__name__icontains=query) |
            Q(brand__name__icontains=query)
        )

        # Agar aniq natija kam bo'lsa, similarity search
        if exact_results.count() < 10:
            try:
                # Trigram similarity (PostgreSQL uchun)
                similar_results = queryset.annotate(
                    similarity=TrigramSimilarity('name', query)
                ).filter(similarity__gt=0.1).order_by('-similarity')

                # Exact va similar natijalarni birlashtirish
                product_ids = list(exact_results.values_list('id', flat=True))
                for product in similar_results:
                    if product.id not in product_ids:
                        exact_results = exact_results.union(
                            queryset.filter(id=product.id)
                        )
            except:
                # Agar PostgreSQL bo'lmasa
                pass

        return exact_results.order_by('-views_count', '-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query'] = self.request.GET.get('q', '')
        context['total_found'] = self.get_queryset().count()
        return context


class FeaturedProductsView(ListView):
    """Tavsiya qilingan mahsulotlar"""
    model = Product
    template_name = 'products/featured_products.html'
    context_object_name = 'products'
    paginate_by = 24

    def get_queryset(self):
        return Product.objects.filter(
            is_featured=True,
            is_active=True,
            in_stock=True
        ).select_related('category', 'brand').order_by('?')


class PopularProductsView(ListView):
    """Eng ko'p sotilgan mahsulotlar"""
    model = Product
    template_name = 'products/popular_products.html'
    context_object_name = 'products'
    paginate_by = 24

    def get_queryset(self):
        return Product.objects.filter(
            is_active=True,
            in_stock=True
        ).select_related('category', 'brand').order_by('-views_count')


class MostLikedProductsView(ListView):
    """Eng ko'p like bosilgan mahsulotlar"""
    model = Product
    template_name = 'products/liked_products.html'
    context_object_name = 'products'
    paginate_by = 24

    def get_queryset(self):
        return Product.objects.filter(
            is_active=True,
            in_stock=True
        ).select_related('category', 'brand').order_by('-likes_count')


@require_POST
@login_required
def product_like_toggle(request, product_id):
    """Mahsulotni like/unlike qilish - AJAX"""
    try:
        product = get_object_or_404(Product, id=product_id, is_active=True)

        like, created = UserLike.objects.get_or_create(
            user=request.user,
            product=product
        )

        if not created:
            # Agar like mavjud bo'lsa, unlike qilish
            like.delete()
            liked = False
        else:
            liked = True

        # Mahsulot likes_count ni yangilash
        product.likes_count = product.userlike_set.count()
        product.save(update_fields=['likes_count'])

        return JsonResponse({
            'success': True,
            'liked': liked,
            'likes_count': product.likes_count
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
def wishlist_view(request):
    """Sevimli mahsulotlar"""
    wishlist_items = ProductWishlist.objects.filter(
        user=request.user
    ).select_related(
        'product__category', 'product__brand'
    ).order_by('-created_at')

    # Pagination
    paginator = Paginator(wishlist_items, 24)
    page = request.GET.get('page', 1)
    wishlist_page = paginator.get_page(page)

    context = {
        'wishlist_items': wishlist_page,
        'total_items': paginator.count,
    }

    return render(request, 'products/wishlist.html', context)


@require_POST
@login_required
def add_to_wishlist(request, product_id):
    """Sevimlilarga qo'shish - AJAX"""
    try:
        product = get_object_or_404(Product, id=product_id, is_active=True)

        wishlist_item, created = ProductWishlist.objects.get_or_create(
            user=request.user,
            product=product
        )

        if created:
            return JsonResponse({
                'success': True,
                'added': True,
                'message': 'Mahsulot sevimlilarga qo\'shildi'
            })
        else:
            return JsonResponse({
                'success': True,
                'added': False,
                'message': 'Mahsulot allaqachon sevimlilarda'
            })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@require_POST
@login_required
def remove_from_wishlist(request, product_id):
    """Sevimlilardan olib tashlash - AJAX"""
    try:
        product = get_object_or_404(Product, id=product_id, is_active=True)

        wishlist_item = ProductWishlist.objects.filter(
            user=request.user,
            product=product
        ).first()

        if wishlist_item:
            wishlist_item.delete()
            return JsonResponse({
                'success': True,
                'removed': True,
                'message': 'Mahsulot sevimlilardan olib tashlandi'
            })
        else:
            return JsonResponse({
                'success': True,
                'removed': False,
                'message': 'Mahsulot sevimlilarda yo\'q'
            })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


def products_suggestions_api(request):
    """Mahsulot suggestions - AJAX autocomplete uchun"""
    query = request.GET.get('q', '').strip()
    suggestions = []

    if query and len(query) >= 2:
        products = Product.objects.filter(
            Q(name__icontains=query),
            is_active=True
        ).select_related('category', 'brand')[:10]

        for product in products:
            suggestions.append({
                'id': product.id,
                'name': product.name,
                'slug': product.slug,
                'category': product.category.name if product.category else '',
                'brand': product.brand.name if product.brand else '',
                'price_usd': str(product.price_usd),
                'price_som': str(product.price_som),
                'image': product.main_image.url if product.main_image else '',
                'url': product.get_absolute_url(),
            })

    return JsonResponse({'suggestions': suggestions})


def product_quick_view_api(request, product_id):
    """Mahsulot tez ko'rish - AJAX modal uchun"""
    try:
        product = get_object_or_404(
            Product,
            id=product_id,
            is_active=True
        )

        # Foydalanuvchi like qilganmi
        user_liked = False
        if request.user.is_authenticated:
            user_liked = UserLike.objects.filter(
                user=request.user,
                product=product
            ).exists()

        data = {
            'success': True,
            'product': {
                'id': product.id,
                'name': product.name,
                'slug': product.slug,
                'description': product.description[:200] + '...' if len(
                    product.description) > 200 else product.description,
                'price_usd': str(product.price_usd),
                'price_som': str(product.price_som),
                'main_image': product.main_image.url if product.main_image else '',
                'category': product.category.name if product.category else '',
                'brand': product.brand.name if product.brand else '',
                'in_stock': product.in_stock,
                'likes_count': product.likes_count,
                'views_count': product.views_count,
                'user_liked': user_liked,
                'url': product.get_absolute_url(),
            }
        }

        return JsonResponse(data)

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


# products/views.py ga qo'shish
# apps/products/views.py ga qo'shish/o'zgartirish

# from django.views.decorators.http import require_http_methods
# import json


@require_http_methods(["POST"])
def get_products_by_ids(request):
    """Get multiple products by IDs for cart"""
    try:
        data = json.loads(request.body)
        product_ids = data.get('ids', [])

        if not product_ids:
            return JsonResponse({'error': 'Product IDs not provided'}, status=400)

        # Fetch products with related data
        products = Product.objects.filter(
            id__in=product_ids,
            is_active=True
        ).select_related('category', 'brand').values(
            'id', 'name', 'slug', 'price_usd',
            'main_image', 'category__name', 'brand__name',
            'description'
        )

        # Get USD rate from settings
        from apps.core.models import Settings
        try:
            settings = Settings.objects.first()
            usd_rate = float(settings.usd_rate) if settings and settings.usd_rate else 12500.0
        except:
            usd_rate = 12500.0

        # Convert to list and add calculated fields
        products_list = []
        for product in products:
            price_usd = float(product['price_usd'])
            price_uzs = price_usd * usd_rate

            products_list.append({
                'id': product['id'],
                'name': product['name'],
                'slug': product['slug'],
                'price_usd': price_usd,
                'price_uzs': price_uzs,  # QO'SHILDI
                'image': product['main_image'],
                'category': product['category__name'] or '',
                'brand': product['brand__name'] or '',
                'description': product['description'][:150] + '...' if product['description'] and len(
                    product['description']) > 150 else (product['description'] or '')
            })

        return JsonResponse(products_list, safe=False)

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)



# @require_http_methods(["POST"])
# def get_products_by_ids(request):
#     """Get multiple products by IDs for cart"""
#     try:
#         data = json.loads(request.body)
#         product_ids = data.get('ids', [])
#
#         products = Product.objects.filter(
#             id__in=product_ids,
#             is_active=True
#         ).values(
#             'id', 'name', 'slug', 'price_usd',
#             'main_image', 'category__name', 'brand__name'
#         )
#
#         # Convert to list and add calculated fields
#         products_list = []
#         for product in products:
#             products_list.append({
#                 'id': product['id'],
#                 'name': product['name'],
#                 'slug': product['slug'],
#                 'price_usd': float(product['price_usd']),
#                 'price_uzs': float(product['price_usd']) * 12500,  # Or get from settings
#                 'image': product['main_image'],
#                 'category': product['category__name'],
#                 'brand': product['brand__name'] or ''
#             })
#
#         return JsonResponse(products_list, safe=False)
#
#     except Exception as e:
#         return JsonResponse({'error': str(e)}, status=400)