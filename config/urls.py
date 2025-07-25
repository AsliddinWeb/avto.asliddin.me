# config/urls.py - i18n PATTERNS

"""
URL configuration for config project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# Multi lang
from django.conf.urls.i18n import i18n_patterns

# Admin customization
admin.site.site_header = "Avtokontinent.uz Admin Panel"
admin.site.site_title = "Avtokontinent Admin"
admin.site.index_title = "Boshqaruv paneli"

# NON-i18n URLs
urlpatterns = [
    path('admin/', admin.site.urls),
    path('i18n/', include('django.conf.urls.i18n')),
]

# i18n URLs (/uz/, /ru/, /en/)
urlpatterns += i18n_patterns(
    path('auth/', include('apps.telegram_auth.urls')),
    path('products/', include('apps.products.urls')),
    path('users/', include('apps.users.urls', namespace='users')),
    path('orders/', include('apps.orders.urls', namespace='orders')),
    path('reviews/', include('apps.reviews.urls', namespace='reviews')),
    path('brands/', include('apps.brands.urls', namespace='brands')),
    path('categories/', include('apps.categories.urls', namespace='categories')),
    path('cart/', include('apps.cart.urls', namespace='cart')),
    path('', include('apps.core.urls')),

    prefix_default_language=False,  # Default til uchun prefix yo'q (/uz/ bo'lmaydi)
)

# Media fayllar uchun (development)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Error handlers
handler404 = 'apps.core.views.handler404'
handler403 = 'apps.core.views.handler403'
handler500 = 'apps.core.views.handler500'
handler400 = 'apps.core.views.handler400'
