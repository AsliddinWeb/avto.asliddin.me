# apps/categories/views.py
from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import JsonResponse

from .models import Category
from apps.products.models import Product
from apps.brands.models import Brand


class CategoryListView(ListView):
    """Barcha kategoriyalar ro'yxati"""
    model = Category
    template_name = 'categories/category_list.html'
    context_object_name = 'categories'
    paginate_by = 20

    def get_queryset(self):
        return Category.objects.filter(
            is_active=True,
            parent=None  # Faqat asosiy kategoriyalar
        ).annotate(
            products_count=Count('product', filter=Q(product__is_active=True))
        ).order_by('order', 'name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Har bir kategoriya uchun subcategories qo'shish
        for category in context['categories']:
            category.subcategories_list = category.get_children()

        return context


class CategoryDetailView(DetailView):
    """Kategoriya detali sahifasi"""
    model = Category
    template_name = 'categories/category_detail.html'
    context_object_name = 'category'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def get_queryset(self):
        return Category.objects.filter(is_active=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category = self.object

        # Subcategoriyalar
        context['subcategories'] = category.get_children()

        # Agar bu parent kategoriya bo'lsa, subcategories va products ko'rsatish
        if category.is_parent:
            # Barcha subcategories'dagi mahsulotlar
            subcategory_ids = category.subcategories.filter(is_active=True).values_list('id', flat=True)
            all_category_ids = list(subcategory_ids) + [category.id]

            context['products'] = Product.objects.filter(
                category_id__in=all_category_ids,
                is_active=True,
                in_stock=True
            ).select_related('category', 'brand').order_by('-created_at')[:12]

        else:
            # Agar subcategory bo'lsa, faqat shu kategoriyadagi mahsulotlar
            context['products'] = Product.objects.filter(
                category=category,
                is_active=True,
                in_stock=True
            ).select_related('category', 'brand').order_by('-created_at')[:12]

        # Mahsulotlar soni
        context['total_products'] = context['products'].count()

        # Bu kategoriyada ishlatiladigan brendlar
        context['category_brands'] = Brand.objects.filter(
            product__category=category,
            product__is_active=True,
            is_active=True
        ).distinct().order_by('name')[:10]

        # Breadcrumb uchun parent kategoriya
        context['parent_category'] = category.parent

        return context


def category_products_view(request, slug):
    """Kategoriya mahsulotlari - pagination bilan"""
    category = get_object_or_404(Category, slug=slug, is_active=True)

    # Filter parametrlari
    brand_filter = request.GET.get('brand')
    sort_by = request.GET.get('sort', '-created_at')  # default: yangi mahsulotlar
    page = request.GET.get('page', 1)

    # Base queryset
    if category.is_parent:
        # Parent kategoriya bo'lsa, barcha subcategories'dan mahsulotlar
        subcategory_ids = category.subcategories.filter(is_active=True).values_list('id', flat=True)
        all_category_ids = list(subcategory_ids) + [category.id]
        products_qs = Product.objects.filter(
            category_id__in=all_category_ids,
            is_active=True,
            in_stock=True
        )
    else:
        # Subcategory bo'lsa, faqat shu kategoriya
        products_qs = Product.objects.filter(
            category=category,
            is_active=True,
            in_stock=True
        )

    # Brand filter
    if brand_filter:
        products_qs = products_qs.filter(brand__slug=brand_filter)

    # Sorting
    sort_options = {
        'name': 'name',
        '-name': '-name',
        'price': 'price_usd',
        '-price': '-price_usd',
        'popular': '-views_count',
        'liked': '-likes_count',
        '-created_at': '-created_at',
        'created_at': 'created_at',
    }

    if sort_by in sort_options:
        products_qs = products_qs.order_by(sort_options[sort_by])

    # Select related for optimization
    products_qs = products_qs.select_related('category', 'brand')

    # Pagination
    paginator = Paginator(products_qs, 24)  # 24 mahsulot per page
    products_page = paginator.get_page(page)

    # Bu kategoriyada mavjud brendlar (filter uchun)
    available_brands = Brand.objects.filter(
        product__category=category,
        product__is_active=True,
        is_active=True
    ).distinct().order_by('name')

    context = {
        'category': category,
        'products': products_page,
        'total_products': paginator.count,
        'available_brands': available_brands,
        'current_brand': brand_filter,
        'current_sort': sort_by,
        'subcategories': category.get_children(),
        'parent_category': category.parent,
    }

    return render(request, 'categories/category_products.html', context)


def subcategory_view(request, parent_slug, slug):
    """Subcategoriya sahifasi"""
    parent_category = get_object_or_404(Category, slug=parent_slug, is_active=True)
    subcategory = get_object_or_404(
        Category,
        slug=slug,
        parent=parent_category,
        is_active=True
    )

    # Subcategoriya mahsulotlari
    products = Product.objects.filter(
        category=subcategory,
        is_active=True,
        in_stock=True
    ).select_related('category', 'brand').order_by('-created_at')

    # Pagination
    paginator = Paginator(products, 24)
    page = request.GET.get('page', 1)
    products_page = paginator.get_page(page)

    context = {
        'category': subcategory,
        'parent_category': parent_category,
        'products': products_page,
        'total_products': paginator.count,
    }

    return render(request, 'categories/subcategory_detail.html', context)


def category_menu_api(request):
    """Kategoriyalar menu - AJAX uchun"""
    categories = Category.objects.filter(
        is_active=True,
        parent=None
    ).prefetch_related(
        'subcategories'
    ).order_by('order')

    menu_data = []
    for category in categories:
        subcategories_data = []
        for sub in category.subcategories.filter(is_active=True):
            subcategories_data.append({
                'id': sub.id,
                'name': sub.name,
                'slug': sub.slug,
                'url': f'/categories/{category.slug}/{sub.slug}/',
            })

        menu_data.append({
            'id': category.id,
            'name': category.name,
            'slug': category.slug,
            'url': f'/categories/{category.slug}/',
            'subcategories': subcategories_data,
        })

    return JsonResponse({'categories': menu_data})


class CategorySearchView(ListView):
    """Kategoriya ichida qidiruv"""
    model = Product
    template_name = 'categories/category_search.html'
    context_object_name = 'products'
    paginate_by = 24

    def get_queryset(self):
        self.category = get_object_or_404(
            Category,
            slug=self.kwargs['slug'],
            is_active=True
        )
        query = self.request.GET.get('q', '')

        if query:
            # Kategoriya ichida qidiruv
            if self.category.is_parent:
                # Parent kategoriya bo'lsa
                subcategory_ids = self.category.subcategories.filter(is_active=True).values_list('id', flat=True)
                all_category_ids = list(subcategory_ids) + [self.category.id]

                return Product.objects.filter(
                    Q(name__icontains=query) | Q(description__icontains=query),
                    category_id__in=all_category_ids,
                    is_active=True,
                    in_stock=True
                ).select_related('category', 'brand')
            else:
                return Product.objects.filter(
                    Q(name__icontains=query) | Q(description__icontains=query),
                    category=self.category,
                    is_active=True,
                    in_stock=True
                ).select_related('category', 'brand')

        return Product.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        context['query'] = self.request.GET.get('q', '')
        context['parent_category'] = self.category.parent
        return context