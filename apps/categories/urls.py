# apps/categories/urls.py
from django.urls import path
from . import views

app_name = 'categories'

urlpatterns = [
    # Kategoriyalar ro'yxati
    path('', views.CategoryListView.as_view(), name='category_list'),

    # API endpoints (AJAX)
    path('api/menu/', views.category_menu_api, name='category_menu_api'),

    # Kategoriya detali
    path('<slug:slug>/', views.CategoryDetailView.as_view(), name='category_detail'),  # ✅

    # Kategoriya mahsulotlari (filter va pagination bilan)
    path('<slug:slug>/products/', views.category_products_view, name='category_products'),

    # Kategoriya ichida qidiruv
    path('<slug:slug>/search/', views.CategorySearchView.as_view(), name='category_search'),

    # Subcategoriya (Parent kategoriya + subcategoriya)
    path('<slug:parent_slug>/<slug:slug>/', views.subcategory_view, name='subcategory_detail'),
]