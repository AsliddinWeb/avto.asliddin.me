# apps/brands/urls.py
from django.urls import path
from . import views

app_name = 'brands'

urlpatterns = [
    # Brendlar ro'yxati
    path('', views.BrandListView.as_view(), name='brand_list'),

    # API endpoints (AJAX)
    path('api/brands/', views.brands_api, name='brands_api'),
    path('api/<slug:brand_slug>/models/', views.car_models_api, name='car_models_api'),

    # Brend detali
    path('<slug:slug>/', views.BrandDetailView.as_view(), name='brand_detail'),

    # Brend mahsulotlari
    path('<slug:slug>/products/', views.brand_products_view, name='brand_products'),

    # Brend avtomobil modellari
    path('<slug:brand_slug>/models/', views.CarModelListView.as_view(), name='car_model_list'),

    # Brend + Kategoriya kombinatsiyasi
    path('<slug:brand_slug>/category/<slug:category_slug>/', views.brand_category_products_view,
         name='brand_category_products'),

    # Avtomobil modeli detali
    path('<slug:brand_slug>/<slug:model_slug>/', views.CarModelDetailView.as_view(), name='car_model_detail'),

    # Avtomobil modeli mahsulotlari
    path('<slug:brand_slug>/<slug:model_slug>/products/', views.car_model_products_view, name='car_model_products'),
]