# config/urls.py
"""
URL configuration for config project.
"""
from django.contrib import admin
from django.urls import path, include

# Static settings
from django.conf import settings
from django.conf.urls.static import static

# Admin customization
admin.site.site_header = "Avtokontinent.uz Admin Panel"
admin.site.site_title = "Avtokontinent Admin"
admin.site.index_title = "Boshqaruv paneli"

# Admin site descriptions
admin.site.site_url = "https://avtokontinent.uz"  # "Saytni ko'rish" tugmasi
admin.site.enable_nav_sidebar = True  # Sidebar navigation

urlpatterns = [
    path('admin/', admin.site.urls),

    # YANGI: Telegram auth URLs
    path('auth/', include('apps.telegram_auth.urls')),

    path('', include('apps.core.urls')),
    path('products/', include('apps.products.urls')),

    # YANGI: Users, Orders, Reviews
    path('users/', include('apps.users.urls', namespace='users')),
    path('orders/', include('apps.orders.urls', namespace='orders')),
    path('reviews/', include('apps.reviews.urls', namespace='reviews')),
    path('brands/', include('apps.brands.urls', namespace='brands')),
    path('categories/', include('apps.categories.urls', namespace='categories')),
    path('cart/', include('apps.cart.urls', namespace='cart')),
]

# Media fayllar uchun (development)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)