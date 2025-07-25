from django.contrib import admin
from modeltranslation.admin import TranslationAdmin
from .models import Category


@admin.register(Category)
class CategoryAdmin(TranslationAdmin):
    list_display = ['name', 'parent', 'is_active', 'order']
    list_filter = ['is_active', 'parent', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['is_active', 'order']
    ordering = ['order', 'name']