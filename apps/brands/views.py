# apps/brands/views.py - TUZATILGAN
from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import JsonResponse

from .models import Brand, CarModel
from apps.products.models import Product
from apps.categories.models import Category


class BrandListView(ListView):
    """Brendlar ro'yxati"""
    model = Brand
    template_name = 'brands/brand_list.html'
    context_object_name = 'brands'
    paginate_by = 24

    def get_queryset(self):
        return Brand.objects.filter(
            is_active=True
        ).annotate(
            products_count=Count('product', filter=Q(product__is_active=True)),
            models_count=Count('car_models', filter=Q(car_models__is_active=True))
        ).order_by('order', 'name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Eng ko'p mahsuloti bo'lgan brendlar
        context['popular_brands'] = Brand.objects.filter(
            is_active=True
        ).annotate(
            products_count=Count('product', filter=Q(product__is_active=True))
        ).order_by('-products_count')[:12]

        return context


class BrandDetailView(DetailView):
    """Brend detali sahifasi"""
    model = Brand
    template_name = 'brands/brand_detail.html'
    context_object_name = 'brand'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def get_queryset(self):
        return Brand.objects.filter(is_active=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        brand = self.object

        # Brend avtomobil modellari
        context['car_models'] = brand.car_models.filter(
            is_active=True
        ).order_by('name')

        # Brend mahsulotlari (oxirgi qo'shilganlar)
        context['recent_products'] = Product.objects.filter(
            brand=brand,
            is_active=True,
            in_stock=True
        ).select_related('category').order_by('-created_at')[:12]

        # Brend mahsulotlari soni
        context['total_products'] = Product.objects.filter(
            brand=brand,
            is_active=True
        ).count()

        # Bu brenddagi kategoriyalar
        context['brand_categories'] = Category.objects.filter(
            product__brand=brand,
            product__is_active=True,
            is_active=True
        ).distinct().order_by('name')

        # Brendning eng mashhur mahsulotlari
        context['popular_products'] = Product.objects.filter(
            brand=brand,
            is_active=True,
            in_stock=True
        ).select_related('category').order_by('-views_count')[:8]

        return context


class CarModelListView(ListView):
    """Brend avtomobil modellari"""
    model = CarModel
    template_name = 'brands/car_models.html'
    context_object_name = 'car_models'
    paginate_by = 24

    def get_queryset(self):
        self.brand = get_object_or_404(Brand, slug=self.kwargs['brand_slug'], is_active=True)
        return CarModel.objects.filter(
            brand=self.brand,
            is_active=True
        ).annotate(
            # TUZATILDI: products o'rniga product_set
            products_count=Count('product', filter=Q(product__is_active=True))
        ).order_by('name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['brand'] = self.brand
        return context


class CarModelDetailView(DetailView):
    """Avtomobil modeli detali"""
    model = CarModel
    template_name = 'brands/car_model_detail.html'
    context_object_name = 'car_model'
    slug_field = 'slug'
    slug_url_kwarg = 'model_slug'

    def get_queryset(self):
        self.brand = get_object_or_404(Brand, slug=self.kwargs['brand_slug'], is_active=True)
        return CarModel.objects.filter(
            brand=self.brand,
            is_active=True
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        car_model = self.object

        context['brand'] = self.brand

        # Model uchun mahsulotlar
        context['model_products'] = Product.objects.filter(
            car_models=car_model,
            is_active=True,
            in_stock=True
        ).select_related('category', 'brand').order_by('-created_at')[:12]

        # Model mahsulotlari soni
        context['total_products'] = Product.objects.filter(
            car_models=car_model,
            is_active=True
        ).count()

        # Bu modeldagi kategoriyalar
        context['model_categories'] = Category.objects.filter(
            product__car_models=car_model,
            product__is_active=True,
            is_active=True
        ).distinct().order_by('name')

        return context


def brand_products_view(request, slug):
    """Brend mahsulotlari - filter va pagination bilan"""
    brand = get_object_or_404(Brand, slug=slug, is_active=True)

    # Filter parametrlari
    category_filter = request.GET.get('category')
    car_model_filter = request.GET.get('model')
    sort_by = request.GET.get('sort', '-created_at')
    page = request.GET.get('page', 1)

    # Base queryset
    products_qs = Product.objects.filter(
        brand=brand,
        is_active=True,
        in_stock=True
    )

    # Category filter
    if category_filter:
        products_qs = products_qs.filter(category__slug=category_filter)

    # Car model filter
    if car_model_filter:
        products_qs = products_qs.filter(car_models__slug=car_model_filter)

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
    paginator = Paginator(products_qs, 24)
    products_page = paginator.get_page(page)

    # Filter options
    available_categories = Category.objects.filter(
        product__brand=brand,
        product__is_active=True,
        is_active=True
    ).distinct().order_by('name')

    # TUZATILDI: products o'rniga product
    available_models = CarModel.objects.filter(
        brand=brand,
        product__is_active=True,
        is_active=True
    ).distinct().order_by('name')

    context = {
        'brand': brand,
        'products': products_page,
        'total_products': paginator.count,
        'available_categories': available_categories,
        'available_models': available_models,
        'current_category': category_filter,
        'current_model': car_model_filter,
        'current_sort': sort_by,
    }

    return render(request, 'brands/brand_products.html', context)


def car_model_products_view(request, brand_slug, model_slug):
    """Avtomobil modeli mahsulotlari"""
    brand = get_object_or_404(Brand, slug=brand_slug, is_active=True)
    car_model = get_object_or_404(
        CarModel,
        brand=brand,
        slug=model_slug,
        is_active=True
    )

    # Filter parametrlari
    category_filter = request.GET.get('category')
    sort_by = request.GET.get('sort', '-created_at')
    page = request.GET.get('page', 1)

    # Base queryset
    products_qs = Product.objects.filter(
        car_models=car_model,
        is_active=True,
        in_stock=True
    )

    # Category filter
    if category_filter:
        products_qs = products_qs.filter(category__slug=category_filter)

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

    # Select related
    products_qs = products_qs.select_related('category', 'brand')

    # Pagination
    paginator = Paginator(products_qs, 24)
    products_page = paginator.get_page(page)

    # Available categories for this model
    available_categories = Category.objects.filter(
        product__car_models=car_model,
        product__is_active=True,
        is_active=True
    ).distinct().order_by('name')

    context = {
        'brand': brand,
        'car_model': car_model,
        'products': products_page,
        'total_products': paginator.count,
        'available_categories': available_categories,
        'current_category': category_filter,
        'current_sort': sort_by,
    }

    return render(request, 'brands/car_model_products.html', context)


def brand_category_products_view(request, brand_slug, category_slug):
    """Brend + Kategoriya kombinatsiyasi"""
    brand = get_object_or_404(Brand, slug=brand_slug, is_active=True)
    category = get_object_or_404(Category, slug=category_slug, is_active=True)

    # Filter parametrlari
    car_model_filter = request.GET.get('model')
    sort_by = request.GET.get('sort', '-created_at')
    page = request.GET.get('page', 1)

    # Base queryset
    products_qs = Product.objects.filter(
        brand=brand,
        category=category,
        is_active=True,
        in_stock=True
    )

    # Car model filter
    if car_model_filter:
        products_qs = products_qs.filter(car_models__slug=car_model_filter)

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

    # Select related
    products_qs = products_qs.select_related('category', 'brand')

    # Pagination
    paginator = Paginator(products_qs, 24)
    products_page = paginator.get_page(page)

    # Available models for this brand+category combination
    available_models = CarModel.objects.filter(
        brand=brand,
        product__category=category,
        product__is_active=True,
        is_active=True
    ).distinct().order_by('name')

    context = {
        'brand': brand,
        'category': category,
        'products': products_page,
        'total_products': paginator.count,
        'available_models': available_models,
        'current_model': car_model_filter,
        'current_sort': sort_by,
    }

    return render(request, 'brands/brand_category_products.html', context)


def brands_api(request):
    """Brendlar API - AJAX uchun"""
    brands = Brand.objects.filter(is_active=True).order_by('name')

    brands_data = []
    for brand in brands:
        brands_data.append({
            'id': brand.id,
            'name': brand.name,
            'slug': brand.slug,
            'logo': brand.logo.url if brand.logo else None,
            'url': f'/brands/{brand.slug}/',
        })

    return JsonResponse({'brands': brands_data})


def car_models_api(request, brand_slug):
    """Brend avtomobil modellari API - AJAX uchun"""
    brand = get_object_or_404(Brand, slug=brand_slug, is_active=True)
    car_models = CarModel.objects.filter(
        brand=brand,
        is_active=True
    ).order_by('name')

    models_data = []
    for model in car_models:
        models_data.append({
            'id': model.id,
            'name': model.name,
            'slug': model.slug,
            'year_from': model.year_from,
            'year_to': model.year_to,
            'url': f'/brands/{brand.slug}/{model.slug}/',
        })

    return JsonResponse({'car_models': models_data})