from django.contrib import admin
from django.utils.html import format_html
from .models import Product, ProductImage, UserLike


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ['image', 'order']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'category', 'brand', 'price_usd', 'price_som_display',
        'is_active', 'is_featured', 'in_stock', 'views_count', 'likes_count'
    ]
    list_filter = [
        'is_active', 'is_featured', 'in_stock', 'category', 'brand', 'created_at'
    ]
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['is_active', 'is_featured', 'in_stock']
    readonly_fields = ['views_count', 'likes_count', 'created_at', 'updated_at']
    inlines = [ProductImageInline]

    fieldsets = (
        ('Asosiy ma\'lumotlar', {
            'fields': ('name', 'slug', 'description', 'main_image')
        }),
        ('Kategoriya va Brand', {
            'fields': ('category', 'brand', 'car_models')
        }),
        ('Narx', {
            'fields': ('price_usd',)
        }),
        ('Video', {
            'fields': ('video_url',)
        }),
        ('Holatlar', {
            'fields': ('is_active', 'is_featured', 'in_stock')
        }),
        ('Statistika', {
            'fields': ('views_count', 'likes_count', 'created_at', 'updated_at')
        }),
    )

    filter_horizontal = ['car_models']

    def price_som_display(self, obj):
        return format_html(
            '<span style="color: green; font-weight: bold;">{}</span>',
            obj.formatted_price_som
        )

    price_som_display.short_description = 'Narxi (UZS)'


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ['product', 'order', 'image']
    list_filter = ['product__category', 'order']
    search_fields = ['product__name']
    list_editable = ['order']


@admin.register(UserLike)
class UserLikeAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'created_at']
    list_filter = ['created_at', 'product__category']
    search_fields = ['user__phone', 'product__name']
    readonly_fields = ['created_at']

    def has_add_permission(self, request):
        return False  # Faqat frontend orqali