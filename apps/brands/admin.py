from django.contrib import admin
from .models import Brand, CarModel

@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'order']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['is_active', 'order']

@admin.register(CarModel)
class CarModelAdmin(admin.ModelAdmin):
    list_display = ['name', 'brand', 'year_from', 'year_to', 'is_active']
    list_filter = ['is_active', 'brand', 'year_from']
    search_fields = ['name', 'brand__name']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['is_active']
    ordering = ['brand__name', 'name']