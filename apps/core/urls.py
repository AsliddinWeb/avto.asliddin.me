# apps/core/urls.py
from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # Bosh sahifa
    path('', views.HomePageView.as_view(), name='homepage'),

    # Statik sahifalar
    path('about/', views.AboutPageView.as_view(), name='about'),
    path('contact/', views.ContactPageView.as_view(), name='contact'),
    path('oferta/', views.OfertaPageView.as_view(), name='oferta'),

    # Qidiruv
    path('search/', views.search_view, name='search'),
    path('global-search/', views.GlobalSearchView.as_view(), name='global_search'),

    # API endpoints (AJAX)
    path('api/search-suggestions/', views.search_suggestions_api, name='search_suggestions_api'),
]