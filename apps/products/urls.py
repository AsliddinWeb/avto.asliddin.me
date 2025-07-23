# apps/products/urls.py
from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    # Mahsulotlar ro'yxati
    path('', views.ProductListView.as_view(), name='product_list'),

    # Maxsus ro'yxatlar
    path('featured/', views.FeaturedProductsView.as_view(), name='featured_products'),
    path('popular/', views.PopularProductsView.as_view(), name='popular_products'),
    path('liked/', views.MostLikedProductsView.as_view(), name='most_liked_products'),

    # Qidiruv
    path('search/', views.ProductSearchView.as_view(), name='product_search'),

    # Sevimlilar (Wishlist)
    path('wishlist/', views.wishlist_view, name='wishlist'),

    # API endpoints (AJAX)
    path('api/suggestions/', views.products_suggestions_api, name='products_suggestions_api'),
    path('api/<int:product_id>/like/', views.product_like_toggle, name='product_like_toggle'),
    path('api/<int:product_id>/quick-view/', views.product_quick_view_api, name='product_quick_view_api'),
    path('api/<int:product_id>/wishlist/add/', views.add_to_wishlist, name='add_to_wishlist'),
    path('api/<int:product_id>/wishlist/remove/', views.remove_from_wishlist, name='remove_from_wishlist'),

    # Mahsulot detali (oxirida bo'lishi kerak - slug conflict oldini olish uchun)
    path('<slug:slug>/', views.ProductDetailView.as_view(), name='product_detail'),

    # products/urls.py ga qo'shish
    path('api/products/by-ids/', views.get_products_by_ids, name='products_by_ids'),
]