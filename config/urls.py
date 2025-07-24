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

urlpatterns = [
    path('admin/', admin.site.urls),

    path('auth/', include('apps.telegram_auth.urls')),

    path('products/', include('apps.products.urls')),
    path('users/', include('apps.users.urls', namespace='users')),
    path('orders/', include('apps.orders.urls', namespace='orders')),
    path('reviews/', include('apps.reviews.urls', namespace='reviews')),
    path('brands/', include('apps.brands.urls', namespace='brands')),
    path('categories/', include('apps.categories.urls', namespace='categories')),
    path('cart/', include('apps.cart.urls', namespace='cart')),

    path('', include('apps.core.urls')),
]

# Error handlers
handler404 = 'django.views.defaults.page_not_found'
handler403 = 'django.views.defaults.permission_denied'
handler500 = 'django.views.defaults.server_error'
handler400 = 'django.views.defaults.bad_request'

# Media fayllar uchun (development)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)