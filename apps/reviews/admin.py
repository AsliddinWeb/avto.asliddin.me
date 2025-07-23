from django.contrib import admin
from .models import Review, ReviewLike, ProductWishlist


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'product', 'rating', 'star_display',
        'is_approved', 'is_featured', 'created_at'  # is_featured QO'SHILDI
    ]
    list_filter = [
        'rating', 'is_approved', 'is_featured', 'created_at'
    ]
    search_fields = [
        'user__phone', 'product__name', 'comment'
    ]
    list_editable = ['is_approved', 'is_featured']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Sharh ma\'lumotlari', {
            'fields': ('user', 'product', 'rating', 'comment')
        }),
        ('Moderatsiya', {
            'fields': ('is_approved', 'is_featured')
        }),
        ('Admin javobi', {
            'fields': ('admin_response', 'admin_response_at')
        }),
        ('Vaqt', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(ProductWishlist)
class ProductWishlistAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__phone', 'product__name']